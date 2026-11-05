export type Priority = 'high' | 'medium' | 'low';
export type ContentType = 'blog_post' | 'landing_page' | 'faq';

export interface ContentRecommendation {
  recommendation_uuid: string;
  target_query_uuid: string;
  target_query_text: string;
  content_type: ContentType;
  title: string;
  rationale: string;
  target_keywords: string[];
  priority: Priority;
  created_at: string;
}

export interface RecommendationListResponse {
  items: ContentRecommendation[];
}
