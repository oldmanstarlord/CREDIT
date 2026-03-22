import api from './api';

export interface NomineeData {
  full_name: string;
  relationship: string;
  phone_number: string;
  aadhaar_number?: string;
  employment_type?: string;
  monthly_income?: number;
  collateral_type?: string;
  collateral_value?: number;
}

export interface ApplicationSubmitPayload {
  full_name: string;
  date_of_birth: string;
  gender?: string;
  phone_number: string;
  email: string;
  aadhaar_number?: string;
  user_category: string;
  category_data: Record<string, unknown>;
  nominee?: NomineeData;
  requested_amount: number;
  requested_tenure_months: number;
  loan_purpose?: string;
}

export interface ApplicationResponse {
  application_id: string;
  application_number: string;
  status: string;
  created_at: string;
  fraud_check_passed: boolean;
  fraud_score?: number;
  next_step: string;
}

export interface CreditScoreResponse {
  credit_score: number;
  score_band: string;
  probability_of_default: number;
  risk_tier: string;
  eligibility: string;
  suggested_amount?: number;
  suggested_tenure_months?: number;
  interest_rate_min?: number;
  interest_rate_max?: number;
  estimated_emi_min?: number;
  estimated_emi_max?: number;
  income_stability_score: number;
  repayment_capacity_score: number;
  spending_data_score: number;
  profile_completeness_score: number;
  alternative_data_score: number;
  top_positive_factors: string[];
  top_negative_factors: string[];
  shap_summary?: string;
}

export interface SimulatePayload {
  application_id: string;
  adjusted_income_percentage?: number;
  adjusted_loan_amount?: number;
  adjusted_tenure_months?: number;
}

export interface SimulateResponse {
  adjusted_credit_score: number;
  adjusted_probability_of_default: number;
  adjusted_eligibility: string;
  adjusted_approved_amount?: number;
  adjusted_interest_rate_min?: number;
  adjusted_interest_rate_max?: number;
  adjusted_emi?: number;
  score_change: number;
  pd_change: number;
}

export const applicationService = {
  submit: (data: ApplicationSubmitPayload) =>
    api.post<ApplicationResponse>('/applications/submit', data),
  getStatus: (id: string) =>
    api.get(`/applications/${id}/status`),
  getScore: (id: string) =>
    api.get<CreditScoreResponse>(`/applications/${id}/score`),
  simulate: (id: string, data: SimulatePayload) =>
    api.post<SimulateResponse>(`/applications/${id}/simulate`, data),
  uploadDocument: (id: string, docType: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/applications/${id}/documents/upload?document_type=${docType}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  appeal: (id: string, reason: string) =>
    api.post(`/applications/${id}/appeal?appeal_reason=${encodeURIComponent(reason)}`),
};
