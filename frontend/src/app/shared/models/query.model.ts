export type VisibilityStatus = 'visible' | 'not_visible' | 'unknown';

export interface DiscoveredQuery {
  query_uuid: string;
  profile_uuid: string;
  run_uuid: string;
  query_text: string;
  estimated_search_volume: number | null;
  competitive_difficulty: number | null;
  opportunity_score: number | null;
  domain_visible: boolean | null;
  visibility_position: number | null;
  status: VisibilityStatus;
  discovered_at: string;
}

export interface QueryFilters {
  minScore?: number;
  status?: VisibilityStatus | null;
  page?: number;
  perPage?: number;
}

export interface PagedQueries {
  items: DiscoveredQuery[];
  page: number;
  per_page: number;
  total: number;
  pages: number;
}
