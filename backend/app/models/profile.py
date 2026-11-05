from app.extensions import db
from app.models.base import iso, new_uuid, utc_now


class BusinessProfile(db.Model):
    __tablename__ = "business_profiles"

    uuid = db.Column(db.String(36), primary_key=True, default=new_uuid)
    name = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(255), nullable=False, index=True)
    industry = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    competitors = db.Column(db.JSON, nullable=False, default=list)
    status = db.Column(db.String(20), nullable=False, default="idle")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    runs = db.relationship(
        "PipelineRun",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="PipelineRun.started_at.desc()",
        lazy="dynamic",
    )
    queries = db.relationship(
        "DiscoveredQuery", back_populates="profile", cascade="all, delete-orphan"
    )
    recommendations = db.relationship(
        "ContentRecommendation", back_populates="profile", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        latest_run = self.runs.first()
        return {
            "profile_uuid": self.uuid,
            "name": self.name,
            "domain": self.domain,
            "industry": self.industry,
            "description": self.description,
            "competitors": self.competitors,
            "status": self.status,
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
            "latest_run": latest_run.to_dict() if latest_run else None,
        }


class PipelineRun(db.Model):
    __tablename__ = "pipeline_runs"

    uuid = db.Column(db.String(36), primary_key=True, default=new_uuid)
    profile_uuid = db.Column(
        db.String(36), db.ForeignKey("business_profiles.uuid"), nullable=False, index=True
    )
    status = db.Column(db.String(20), nullable=False, default="running")
    llm_model = db.Column(db.String(100), nullable=False)
    queries_discovered = db.Column(db.Integer, nullable=False, default=0)
    queries_scored = db.Column(db.Integer, nullable=False, default=0)
    tokens_used = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    completed_at = db.Column(db.DateTime(timezone=True))

    profile = db.relationship("BusinessProfile", back_populates="runs")
    queries = db.relationship("DiscoveredQuery", back_populates="run", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "run_uuid": self.uuid,
            "profile_uuid": self.profile_uuid,
            "profile_name": self.profile.name,
            "status": self.status,
            "llm_model": self.llm_model,
            "queries_discovered": self.queries_discovered,
            "queries_scored": self.queries_scored,
            "tokens_used": self.tokens_used,
            "error_message": self.error_message,
            "started_at": iso(self.started_at),
            "completed_at": iso(self.completed_at),
        }
