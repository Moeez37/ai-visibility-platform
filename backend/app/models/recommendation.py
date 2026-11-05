from app.extensions import db
from app.models.base import iso, new_uuid, utc_now


class ContentRecommendation(db.Model):
    __tablename__ = "content_recommendations"

    uuid = db.Column(db.String(36), primary_key=True, default=new_uuid)
    profile_uuid = db.Column(
        db.String(36), db.ForeignKey("business_profiles.uuid"), nullable=False, index=True
    )
    query_uuid = db.Column(
        db.String(36), db.ForeignKey("discovered_queries.uuid"), nullable=False, index=True
    )
    content_type = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    rationale = db.Column(db.Text, nullable=False)
    target_keywords = db.Column(db.JSON, nullable=False, default=list)
    priority = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    profile = db.relationship("BusinessProfile", back_populates="recommendations")
    target_query = db.relationship("DiscoveredQuery", back_populates="recommendations")

    def to_dict(self) -> dict:
        return {
            "recommendation_uuid": self.uuid,
            "target_query_uuid": self.query_uuid,
            "target_query_text": self.target_query.query_text,
            "content_type": self.content_type,
            "title": self.title,
            "rationale": self.rationale,
            "target_keywords": self.target_keywords,
            "priority": self.priority,
            "created_at": iso(self.created_at),
        }
