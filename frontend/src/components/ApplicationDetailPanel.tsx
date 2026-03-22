import React from 'react';
import { X, User, Calendar, DollarSign, TrendingUp, Shield, FileText } from 'lucide-react';
import CreditScoreGauge from './CreditScoreGauge';
import ShapChart from './ShapChart';
import FraudCheckStatus from './FraudCheckStatus';

interface Application {
  id: string;
  application_number: string;
  user_name: string;
  user_category: string;
  requested_amount: number;
  requested_tenure_months: number;
  loan_purpose: string;
  credit_score?: number;
  probability_of_default?: number;
  risk_band?: string;
  status: string;
  final_decision?: string;
  decision_reason?: string;
  created_at: string;
  fraud_score?: number;
  fraud_check_passed?: boolean;
  ml_scoring_result?: any;
  policy_check_details?: any;
}

interface ApplicationDetailPanelProps {
  application: Application | null;
  onClose: () => void;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  onHold?: (id: string) => void;
}

const ApplicationDetailPanel: React.FC<ApplicationDetailPanelProps> = ({
  application,
  onClose,
  onApprove,
  onReject,
  onHold,
}) => {
  if (!application) return null;

  const shapData = application.ml_scoring_result?.shap_explanation;
  const positiveFactors = shapData?.top_positive_factors || [];
  const negativeFactors = shapData?.top_negative_factors || [];

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/30 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="relative w-full max-w-2xl bg-white shadow-2xl overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 z-10 bg-barclays-navy text-white px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold font-heading">
              {application.application_number}
            </h2>
            <p className="text-sm opacity-80">{application.user_name}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Basic Info */}
          <section>
            <h3 className="text-sm font-semibold text-user-text mb-3 flex items-center gap-2">
              <User size={16} />
              Application Details
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-user-muted">Category</p>
                <p className="text-sm font-medium text-user-text">
                  {application.user_category.replace(/_/g, ' ')}
                </p>
              </div>
              <div>
                <p className="text-xs text-user-muted">Loan Purpose</p>
                <p className="text-sm font-medium text-user-text">
                  {application.loan_purpose}
                </p>
              </div>
              <div>
                <p className="text-xs text-user-muted">Requested Amount</p>
                <p className="text-sm font-medium text-user-text font-data">
                  ₹{application.requested_amount.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-xs text-user-muted">Tenure</p>
                <p className="text-sm font-medium text-user-text">
                  {application.requested_tenure_months} months
                </p>
              </div>
              <div>
                <p className="text-xs text-user-muted">Applied On</p>
                <p className="text-sm font-medium text-user-text">
                  {new Date(application.created_at).toLocaleDateString()}
                </p>
              </div>
              <div>
                <p className="text-xs text-user-muted">Status</p>
                <p className="text-sm font-medium text-user-text">
                  {application.status.replace(/_/g, ' ').toUpperCase()}
                </p>
              </div>
            </div>
          </section>

          {/* Credit Score */}
          {application.credit_score && (
            <section>
              <h3 className="text-sm font-semibold text-user-text mb-3 flex items-center gap-2">
                <TrendingUp size={16} />
                Credit Assessment
              </h3>
              <div className="bg-user-surface rounded-card p-4">
                <CreditScoreGauge score={application.credit_score} animated={false} />
                <div className="mt-4 grid grid-cols-2 gap-4 text-center">
                  <div>
                    <p className="text-xs text-user-muted">Default Probability</p>
                    <p className="text-lg font-semibold text-user-text font-data">
                      {((application.probability_of_default || 0) * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-user-muted">Risk Band</p>
                    <p className="text-lg font-semibold text-user-text">
                      {application.risk_band?.toUpperCase() || 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* Fraud Check */}
          {application.fraud_score !== undefined && (
            <section>
              <h3 className="text-sm font-semibold text-user-text mb-3 flex items-center gap-2">
                <Shield size={16} />
                Fraud Assessment
              </h3>
              <FraudCheckStatus
                fraudScore={application.fraud_score}
                fraudCheckPassed={application.fraud_check_passed || false}
              />
            </section>
          )}

          {/* SHAP Explanation */}
          {positiveFactors.length > 0 && (
            <section>
              <h3 className="text-sm font-semibold text-user-text mb-3 flex items-center gap-2">
                <FileText size={16} />
                Score Factors
              </h3>
              <div className="bg-user-surface rounded-card p-4">
                <ShapChart
                  positiveFactors={positiveFactors}
                  negativeFactors={negativeFactors}
                  compact={false}
                />
              </div>
            </section>
          )}

          {/* Decision Reason */}
          {application.decision_reason && (
            <section>
              <h3 className="text-sm font-semibold text-user-text mb-3">
                Decision Reason
              </h3>
              <div className="bg-yellow-50 border border-yellow-200 rounded-card p-3">
                <p className="text-sm text-user-text">
                  {application.decision_reason}
                </p>
              </div>
            </section>
          )}

          {/* Action Buttons */}
          {application.status === 'hold' && (
            <section className="flex gap-3">
              {onApprove && (
                <button
                  onClick={() => onApprove(application.id)}
                  className="flex-1 px-4 py-2.5 bg-risk-low text-white rounded-card font-medium hover:bg-green-600 transition-colors"
                >
                  Approve
                </button>
              )}
              {onHold && (
                <button
                  onClick={() => onHold(application.id)}
                  className="flex-1 px-4 py-2.5 bg-risk-medium text-white rounded-card font-medium hover:bg-yellow-600 transition-colors"
                >
                  Keep on Hold
                </button>
              )}
              {onReject && (
                <button
                  onClick={() => onReject(application.id)}
                  className="flex-1 px-4 py-2.5 bg-risk-very_high text-white rounded-card font-medium hover:bg-red-600 transition-colors"
                >
                  Reject
                </button>
              )}
            </section>
          )}
        </div>
      </div>
    </div>
  );
};

export default ApplicationDetailPanel;
