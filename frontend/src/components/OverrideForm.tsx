import React, { useState } from 'react';
import { AlertTriangle, Lock, FileText } from 'lucide-react';

interface OverrideFormProps {
  applicationId: string;
  currentDecision: string;
  proposedDecision: 'approve' | 'reject';
  onSubmit: (justification: string, approverPassword: string) => Promise<void>;
  onCancel: () => void;
}

const OverrideForm: React.FC<OverrideFormProps> = ({
  applicationId,
  currentDecision,
  proposedDecision,
  onSubmit,
  onCancel,
}) => {
  const [justification, setJustification] = useState('');
  const [approverPassword, setApproverPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (justification.length < 50) {
      setError('Justification must be at least 50 characters');
      return;
    }

    if (!approverPassword) {
      setError('Approver password is required');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(justification, approverPassword);
    } catch (err: any) {
      setError(err.message || 'Override failed. Please check your credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-card shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-red-50 border-b border-red-200 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertTriangle size={24} className="text-risk-very_high" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-user-text font-heading">
                Decision Override Required
              </h2>
              <p className="text-sm text-user-muted">
                Overriding {currentDecision} → {proposedDecision}
              </p>
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Warning */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-card p-4">
            <div className="flex gap-3">
              <AlertTriangle size={20} className="text-yellow-600 shrink-0 mt-0.5" />
              <div className="text-sm text-yellow-800 space-y-2">
                <p className="font-semibold">Important: Manual Override</p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li>This action overrides the ML model recommendation</li>
                  <li>Detailed justification is mandatory and will be audited</li>
                  <li>Senior approver credentials are required</li>
                  <li>This decision is logged and cannot be deleted</li>
                  <li>Excessive overrides may trigger compliance review</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Application Info */}
          <div className="bg-user-surface rounded-card p-4">
            <h3 className="text-sm font-semibold text-user-text mb-2 flex items-center gap-2">
              <FileText size={16} />
              Application Details
            </h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-user-muted">Application ID</p>
                <p className="font-medium text-user-text font-data">{applicationId}</p>
              </div>
              <div>
                <p className="text-user-muted">Current Decision</p>
                <p className="font-medium text-user-text">{currentDecision.toUpperCase()}</p>
              </div>
              <div>
                <p className="text-user-muted">Proposed Override</p>
                <p className={`font-medium ${proposedDecision === 'approve' ? 'text-risk-low' : 'text-risk-very_high'}`}>
                  {proposedDecision.toUpperCase()}
                </p>
              </div>
            </div>
          </div>

          {/* Justification */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-user-text">
              Detailed Justification <span className="text-risk-very_high">*</span>
            </label>
            <textarea
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              placeholder="Provide a detailed explanation for this override decision. Include specific reasons, risk assessment, and any mitigating factors..."
              className="w-full px-4 py-3 border border-user-border rounded-card text-sm focus:outline-none focus:border-barclays-navy min-h-[120px]"
              required
              minLength={50}
            />
            <p className="text-xs text-user-muted">
              {justification.length}/50 characters minimum
            </p>
          </div>

          {/* Approver Password */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-user-text">
              Senior Approver Password <span className="text-risk-very_high">*</span>
            </label>
            <div className="relative">
              <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-user-muted" />
              <input
                type="password"
                value={approverPassword}
                onChange={(e) => setApproverPassword(e.target.value)}
                placeholder="Enter approver password"
                className="w-full pl-10 pr-4 py-2.5 border border-user-border rounded-card text-sm focus:outline-none focus:border-barclays-navy"
                required
              />
            </div>
            <p className="text-xs text-user-muted">
              Only Risk Managers and above can authorize overrides
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-card p-3">
              <p className="text-sm text-risk-very_high">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-user-border">
            <button
              type="button"
              onClick={onCancel}
              disabled={isSubmitting}
              className="flex-1 px-4 py-2.5 border border-user-border rounded-card font-medium text-user-text hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || justification.length < 50 || !approverPassword}
              className={`
                flex-1 px-4 py-2.5 rounded-card font-medium text-white transition-colors
                ${proposedDecision === 'approve' ? 'bg-risk-low hover:bg-green-600' : 'bg-risk-very_high hover:bg-red-600'}
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Submitting...
                </span>
              ) : (
                `Confirm Override to ${proposedDecision.toUpperCase()}`
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default OverrideForm;
