export type RunStatus = 'running' | 'completed' | 'failed';

export interface PipelineRun {
  run_uuid: string;
  profile_uuid: string;
  profile_name: string;
  status: RunStatus;
  llm_model: string;
  queries_discovered: number;
  queries_scored: number;
  tokens_used: number;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
}

export interface BusinessProfile {
  profile_uuid: string;
  name: string;
  domain: string;
  industry: string;
  description: string;
  competitors: string[];
  status: 'idle' | RunStatus;
  created_at: string;
  updated_at: string;
  latest_run: PipelineRun | null;
}

export interface ProfileCreateRequest {
  name: string;
  domain: string;
  industry: string;
  description: string;
  competitors: string[];
}

export interface ProfileListResponse {
  items: BusinessProfile[];
}

export interface DashboardSummary {
  total_profiles: number;
  total_queries: number;
  avg_opportunity_score: number | null;
  recent_runs: PipelineRun[];
}
