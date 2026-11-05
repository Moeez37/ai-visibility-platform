import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta

from flask import current_app

from app.agents.base import AgentError, ProfileContext
from app.agents.discovery import QueryDiscoveryAgent
from app.agents.llm import LLMClient, build_llm_client
from app.agents.recommendation import ContentRecommendationAgent, QueryOpportunity
from app.agents.scoring import VisibilityCheck, VisibilityScoringAgent
from app.extensions import db
from app.models import BusinessProfile, ContentRecommendation, DiscoveredQuery, PipelineRun
from app.models.base import utc_now
from app.utils.scoring import opportunity_score

logger = logging.getLogger(__name__)
MAX_QUERIES_FOR_RECOMMENDATIONS = 10


def profile_context(profile: BusinessProfile) -> ProfileContext:
    return ProfileContext(
        name=profile.name,
        domain=profile.domain,
        industry=profile.industry,
        description=profile.description,
        competitors=list(profile.competitors),
    )


def apply_check(query: DiscoveredQuery, check: VisibilityCheck, keep_estimates: bool = False) -> None:
    # A recheck keeps earlier estimates, so a changed score always means changed visibility.
    if not (keep_estimates and query.estimated_search_volume is not None):
        query.estimated_search_volume = check.search_volume
        query.competitive_difficulty = check.difficulty
    query.domain_visible = check.domain_visible
    query.visibility_position = check.position
    query.opportunity_score = opportunity_score(
        query.estimated_search_volume,
        query.competitive_difficulty,
        check.domain_visible,
        check.position,
    )


class PipelineOrchestrator:
    def __init__(self, llm: LLMClient, concurrency: int):
        self.discovery = QueryDiscoveryAgent(llm)
        self.scoring = VisibilityScoringAgent(llm)
        self.recommendation = ContentRecommendationAgent(llm)
        self.concurrency = concurrency

    def execute(self, run_uuid: str) -> None:
        run = db.session.get(PipelineRun, run_uuid)
        profile = run.profile
        problems: list[str] = []
        try:
            context = profile_context(profile)
            queries = self._discover(run, profile, context)
            self._score(run, queries, context, problems)
            if run.queries_scored == 0:
                raise AgentError(f"No query could be scored. {problems[0]}")
            self._recommend(run, queries, context, problems)
            self._finish(run, "completed", " ".join(problems) or None)
        except AgentError as error:
            db.session.rollback()
            run.tokens_used += error.tokens_used
            self._finish(run, "failed", str(error))
        except Exception:
            logger.exception("Pipeline run %s crashed", run_uuid)
            db.session.rollback()
            self._finish(run, "failed", "The pipeline hit an unexpected error.")

    def _discover(
        self, run: PipelineRun, profile: BusinessProfile, context: ProfileContext
    ) -> list[DiscoveredQuery]:
        result = self.discovery.discover(context)
        queries = [
            DiscoveredQuery(profile_uuid=profile.uuid, run_uuid=run.uuid, query_text=text)
            for text in result.output.queries
        ]
        db.session.add_all(queries)
        run.queries_discovered = len(queries)
        run.tokens_used += result.tokens_used
        db.session.commit()
        return queries

    def _score(
        self,
        run: PipelineRun,
        queries: list[DiscoveredQuery],
        context: ProfileContext,
        problems: list[str],
    ) -> None:
        # Worker threads only call the LLM. All database writes stay on this thread.
        failures: list[str] = []
        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            futures = {
                pool.submit(self.scoring.check, query.query_text, context): query
                for query in queries
            }
            for future in as_completed(futures):
                try:
                    check = future.result()
                except AgentError as error:
                    run.tokens_used += error.tokens_used
                    failures.append(str(error))
                    db.session.commit()
                    continue
                apply_check(futures[future], check)
                run.queries_scored += 1
                run.tokens_used += check.tokens_used
                db.session.commit()
        if failures:
            problems.append(
                f"{len(failures)} of {len(queries)} queries could not be scored ({failures[0]})."
            )

    def _recommend(
        self,
        run: PipelineRun,
        queries: list[DiscoveredQuery],
        context: ProfileContext,
        problems: list[str],
    ) -> None:
        candidates = sorted(
            (query for query in queries if query.domain_visible is False),
            key=lambda query: query.opportunity_score,
            reverse=True,
        )[:MAX_QUERIES_FOR_RECOMMENDATIONS]
        if not candidates:
            return

        opportunities = [
            QueryOpportunity(
                query_id=index,
                query_text=query.query_text,
                search_volume=query.estimated_search_volume,
                difficulty=query.competitive_difficulty,
                opportunity_score=query.opportunity_score,
            )
            for index, query in enumerate(candidates, start=1)
        ]
        try:
            result = self.recommendation.recommend(context, opportunities)
        except AgentError as error:
            run.tokens_used += error.tokens_used
            problems.append(f"Recommendations could not be generated ({error}).")
            return

        run.tokens_used += result.tokens_used
        db.session.add_all(
            ContentRecommendation(
                profile_uuid=run.profile_uuid,
                query_uuid=candidates[item.query_id - 1].uuid,
                content_type=item.content_type,
                title=item.title,
                rationale=item.rationale,
                target_keywords=item.target_keywords,
                priority=item.priority,
            )
            for item in result.output.recommendations
        )

    def _finish(self, run: PipelineRun, status: str, error_message: str | None) -> None:
        run.status = status
        run.error_message = error_message
        run.completed_at = utc_now()
        run.profile.status = status
        db.session.commit()


def fail_stale_runs(profile_uuid: str) -> None:
    # A run still marked running after this long lost its thread to a server restart.
    cutoff = utc_now() - timedelta(minutes=current_app.config["STALE_RUN_MINUTES"])
    stale = PipelineRun.query.filter(
        PipelineRun.profile_uuid == profile_uuid,
        PipelineRun.status == "running",
        PipelineRun.started_at < cutoff,
    ).all()
    for run in stale:
        run.status = "failed"
        run.error_message = "The run was interrupted by a server restart."
        run.completed_at = utc_now()
    if stale:
        db.session.commit()


def start_run(profile: BusinessProfile) -> PipelineRun:
    llm = build_llm_client(current_app.config)
    run = PipelineRun(profile_uuid=profile.uuid, llm_model=llm.model_name)
    profile.status = "running"
    db.session.add(run)
    db.session.commit()

    orchestrator = PipelineOrchestrator(llm, current_app.config["SCORING_CONCURRENCY"])
    if current_app.config["PIPELINE_ASYNC"]:
        app = current_app._get_current_object()
        run_uuid = run.uuid

        def work() -> None:
            with app.app_context():
                orchestrator.execute(run_uuid)

        threading.Thread(target=work, daemon=True).start()
    else:
        orchestrator.execute(run.uuid)
    return run


def recheck_query(query: DiscoveredQuery) -> DiscoveredQuery:
    llm = build_llm_client(current_app.config)
    check = VisibilityScoringAgent(llm).check(query.query_text, profile_context(query.profile))
    apply_check(query, check, keep_estimates=True)
    query.run.tokens_used += check.tokens_used
    db.session.commit()
    return query
