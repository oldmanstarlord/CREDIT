import api from './api';

export interface AdminApplication {
  id: string;
  application_number: string;
  user_name: string;
  category: string | null;
  created_at: string;
  status: string;
  fraud_score: number | null;
  credit_score: number | null;
  probability_of_default: number | null;
  requested_amount: number;
  final_decision: string | null;
}

export interface ApplicationsListResponse {
  total: number;
  limit: number;
  offset: number;
  count: number;
  applications: AdminApplication[];
}

export interface ApplicationDetail {
  id: string;
  application_number: string;
  user: { id: string; name: string; email: string; phone: string };
  category: string | null;
  application_data: Record<string, unknown>;
  fraud_check: { fraud_score: number; fraud_decision: string; fraud_details: Record<string, unknown> };
  ml_scoring: {
    credit_score: number | null;
    probability_of_default: number | null;
    risk_band: string | null;
    shap_explanation: {
      base_value: number;
      top_positive_factors: Array<{ feature: string; value: number }>;
      top_negative_factors: Array<{ feature: string; value: number }>;
      plain_english_summary: string;
    } | null;
  };
  policy_check: { all_passed: boolean; details: Record<string, unknown> };
  decision: {
    final_decision: string | null;
    decision_timestamp: string | null;
    decision_reason: string | null;
    override_flag: boolean;
    override_justification: string | null;
  };
  loan_terms: {
    requested_amount: number;
    approved_amount: number | null;
    approved_interest_rate: number | null;
    approved_tenure_months: number | null;
    estimated_emi: number | null;
  };
  audit_trail: Array<{
    event_id: string;
    event_type: string;
    timestamp: string;
    actor_id: string | null;
    input_snapshot: Record<string, unknown> | null;
    model_output: Record<string, unknown> | null;
    policy_results: Record<string, unknown> | null;
  }>;
}

export interface DashboardKPIs {
  period_days: number;
  total_applications: number;
  decisions: { approved: number; rejected: number; held: number; approval_rate_pct: number };
  model_metrics: { avg_credit_score: number; avg_probability_of_default: number };
  portfolio: { total_approved_amount_inr: number; avg_approved_amount_inr: number };
  fraud_detection: { high_fraud_flagged: number; fraud_detection_rate_pct: number };
}

export interface ModelVersion {
  id: string;
  version: string;
  name: string;
  status: 'active' | 'staging' | 'archived';
  accuracy: number;
  auc: number;
  precision: number;
  recall: number;
  f1_score: number;
  deployed_at?: string;
  trained_at: string;
  training_samples: number;
  features_count: number;
  artifact_path: string;
  notes?: string;
}

export interface ModelRegistryResponse {
  total_models: number;
  active_model_version: string;
  models: ModelVersion[];
}

export const adminService = {
  getApplications: (params: {
    stage?: string;
    status_filter?: string;
    category?: string;
    limit?: number;
    offset?: number;
    sort_by?: string;
    sort_order?: string;
  } = {}) => api.get<ApplicationsListResponse>('/admin/applications', { params }),

  getApplicationDetail: (id: string) =>
    api.get<ApplicationDetail>(`/admin/applications/${id}`),

  addNote: (id: string, noteText: string) =>
    api.post(`/admin/applications/${id}/notes?note_text=${encodeURIComponent(noteText)}`),

  makeDecision: (id: string, params: {
    decision: string;
    reason: string;
    approved_amount?: number;
    tenure_months?: number;
    approved_interest_rate?: number;
  }) => api.put(`/admin/applications/${id}/decide`, null, { params }),

  overrideDecision: (id: string, params: {
    override_decision: string;
    justification: string;
  }) => api.post(`/admin/applications/${id}/override`, null, { params }),

  getKPIs: (days?: number) =>
    api.get<DashboardKPIs>('/admin/dashboard/kpis', { params: { days } }),

  getFairnessReport: (days?: number) =>
    api.get('/admin/fairness/report', { params: { days } }),

  getPortfolioRisk: () =>
    api.get('/admin/portfolio/risk'),

  getAuditLogs: (applicationId: string, limit?: number) =>
    api.get(`/admin/audit-logs/${applicationId}`, { params: { limit } }),

  getModelRegistry: () =>
    api.get<ModelRegistryResponse>('/admin/models/registry'),

  deployModel: (modelId: string) =>
    api.post(`/admin/models/${modelId}/deploy`),

  archiveModel: (modelId: string) =>
    api.post(`/admin/models/${modelId}/archive`),
};
