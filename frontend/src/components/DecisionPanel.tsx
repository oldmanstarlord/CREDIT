import React, { useState } from 'react';
import { CheckCircle, XCircle, Clock, AlertTriangle } from 'lucide-react';

interface DecisionPanelProps {
  applicationId: string;
  currentStatus: string;
  onDecision: (decision: 'approve' | 'reject' | 'hold', reason: string) => Promise<void>;
  disabled?: boolean;
}

const DecisionPanel: React.FC<DecisionPanelProps> = ({
  applicationId,
  currentStatus,
  onDecision,
  disabled = false,
}) => {
  const [selectedDecision, setSelectedDecision] = useState<'approve' | 'reject' | 'hold' | null>(null);
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const reasons = {
    approve: [
      'Strong credit profile',
      'Sufficient income verification',
      'Low risk indicators',
      'Policy checks passed',
      'Manual override - acceptable risk',
    ],
    reject: [
      'High fraud risk',
      'Insufficient income',
      'Poor credit history',
      'Failed policy checks',
      'Unverifiable information',
      'Debt burden too high',
    ],
    hold: [
      'Pending document verification',
      'Requires additional information',
      'Borderline risk assessment',
      'Awaiting senior approval',
      'Need collateral verification',
    ],
  };

  const handleSubmit = async () => {
    if (!selectedDecision || !reason) {
      alert('Please select a decision and provide a reason');
      return;
    }

    setIsSubmitting(true);
    try {
      await onDecision(selectedDecision, reason);
      setSelectedDecision(null);
      setReason('');
    } catch (error) {
      alert('Failed to submit decision. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const decisionButtons = [
    {
      id: 'approve' as const,
      label: 'Approve',
      icon: CheckCircle,
      color: 'bg-risk-low hover:bg-green-600',
      textColor: 'text-risk-low',
      bgColor: 'bg-green-50',
    },
    {
      id: 'hold' as const,
      label: 'Hold',
      icon: Clock,
      color: 'bg-risk-medium hover:bg-yellow-600',
      textColor: 'text-risk-medium',
      bgColor: 'bg-yellow-50',
    },
    {
      id: 'reject' as const,
      label: 'Reject',
      icon: XCircle,
      color: 'bg-risk-very_high hover:bg-red-600',
      textColor: 'text-risk-very_high',
      bgColor: 'bg-red-50',
    },
  ];

  return (
    <div className="bg-white border border-user-border rounded-card p-6 space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle size={20} className="text-barclays-navy" />
        <h3 className="text-lg font-semibold text-user-text font-heading">
          Make Decision
        </h3>
      </div>

      {/* Decision Buttons */}
      <div className="grid grid-cols-3 gap-3">
        {decisionButtons.map((btn) => {
          const Icon = btn.icon;
          const isSelected = selectedDecision === btn.id;
          return (
            <button
              key={btn.id}
              onClick={() => setSelectedDecision(btn.id)}
              disabled={disabled}
              className={`
                p-4 rounded-card border-2 transition-all duration-200
                ${isSelected
                  ? `${btn.bgColor} border-current ${btn.textColor}`
                  : 'bg-white border-user-border hover:border-barclays-blue'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <Icon size={24} className={`mx-auto mb-2 ${isSelected ? btn.textColor : 'text-user-muted'}`} />
              <p className={`text-sm font-medium ${isSelected ? btn.textColor : 'text-user-text'}`}>
                {btn.label}
              </p>
            </button>
          );
        })}
      </div>

      {/* Reason Selection */}
      {selectedDecision && (
        <div className="space-y-3 animate-fade-in">
          <label className="block text-sm font-medium text-user-text">
            Select Reason <span className="text-risk-very_high">*</span>
          </label>
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            disabled={disabled}
            className="w-full px-4 py-2.5 border border-user-border rounded-card text-sm focus:outline-none focus:border-barclays-navy disabled:opacity-50"
          >
            <option value="">Choose a reason...</option>
            {reasons[selectedDecision].map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
            <option value="custom">Other (specify below)</option>
          </select>

          {reason === 'custom' && (
            <textarea
              placeholder="Enter custom reason..."
              onChange={(e) => setReason(e.target.value)}
              disabled={disabled}
              className="w-full px-4 py-2.5 border border-user-border rounded-card text-sm focus:outline-none focus:border-barclays-navy disabled:opacity-50 min-h-[80px]"
            />
          )}

          {/* Warning */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-card p-3 flex gap-2">
            <AlertTriangle size={16} className="text-yellow-600 shrink-0 mt-0.5" />
            <p className="text-xs text-yellow-800">
              This decision will be logged in the audit trail and cannot be undone without proper authorization.
            </p>
          </div>

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={!reason || isSubmitting || disabled}
            className={`
              w-full px-4 py-3 rounded-card font-medium text-white transition-all duration-200
              ${decisionButtons.find((b) => b.id === selectedDecision)?.color}
              disabled:opacity-50 disabled:cursor-not-allowed
            `}
          >
            {isSubmitting ? (
              <span className="flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Submitting...
              </span>
            ) : (
              `Confirm ${selectedDecision.charAt(0).toUpperCase() + selectedDecision.slice(1)}`
            )}
          </button>
        </div>
      )}
    </div>
  );
};

export default DecisionPanel;
