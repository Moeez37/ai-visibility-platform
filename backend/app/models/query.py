from app.extensions import db
from app.models.base import iso, new_uuid, utc_now


class DiscoveredQuery(db.Model):
    __tablename__ = "discovered_queries"

    uuid = db.Column(db.String(36), primary_key=True, default=new_uuid)
    profile_uuid = db.Column(
        db.String(36), db.ForeignKey("business_profiles.uuid"), nullable=False, index=True
    )
    run_uuid = db.Column(
        db.String(36), db.ForeignKey("pipeline_runs.uuid"), nullable=False, index=True
    )
    query_text = db.Column(db.Text, nullable=False)
    estimated_search_volume = db.Column(db.Integer)
    competitive_difficulty = db.Column(db.Integer)
    opportunity_score = db.Column(db.Float, index=True)
    # NULL means the check failed, which the API reports as status "unknown".
    domain_visible = db.Column(db.Boolean)
    visibility_position = db.Column(db.Integer)
    discovered_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    profile = db.relationship("BusinessProfile", back_populates="queries")
    run = db.relationship("PipelineRun", back_populates="queries")
    recommendations = db.relationship(
        "ContentRecommendation", back_populates="target_query", cascade="all, delete-orphan"
    )

    @property
    def status(self) -> str:
        if self.domain_visible is None:
            return "unknown"
        return "visible" if self.domain_visible else "not_visible"

    def to_dict(self) -> dict:
        return {
            "query_uuid": self.uuid,
            "profile_uuid": self.profile_uuid,
            "run_uuid": self.run_uuid,
            "query_text": self.query_text,
            "estimated_search_volume": self.estimated_search_volume,
            "competitive_difficulty": self.competitive_difficulty,
            "opportunity_score": self.opportunity_score,
            "domain_visible": self.domain_visible,
            "visibility_position": self.visibility_position,
            "status": self.status,
            "discovered_at": iso(self.discovered_at),
        }
