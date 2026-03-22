import React from 'react';
import { Shield, ShieldAlert, ShieldCheck, AlertTriangle } from 'lucide-react';

interface FraudCheckStatusProps {
  fraudScore: number;
  fraudCheckPassed: boolean;
  fraudDetails?: {
    checks?: Array<{
      name: string;
      passed: boolean;
      score?: number;
    }>;
  };
  compact?: boolean;
}

const FraudCheckStatus: React.FC<FraudCheckStatusProps> = ({
  fraudScore,
  fraudCheckPassed,
  fraudDetails,
  compact = false,
}) => {
  const getStatusConfig = () => {
    if (fraudScore < 0.3) {
      return {
        icon: ShieldCheck,
        label: 'Low Risk',
        color: 'text-risk-low',
        bgColor: 'bg-green-50',
        borderColor: 'border-risk-low',
        message: 'All fraud checks passed successfully',
      };
    }
    if (fraudScore < 0.6) {
      return {
        icon: Shield,
        label: 'Medium Risk',
        color: 'text-risk-medium',
        bgColor: 'bg-yellow-50',
        borderColor: 'border-risk-medium',
        message: 'Some fraud indicators detected, under review',
      };
    }
    return {
      icon: ShieldAlert,
      label: 'High Risk',
      color: 'text-risk-very_high',
      bgColor: 'bg-red-50',
      borderColor: 'border-risk-very_high',
      message: 'Multiple fraud indicators detected, manual review required',
    };
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  if (compact) {
    return (
      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-pill ${config.bgColor} border ${config.borderColor}`}>
        <Icon size={16} className={config.color} />
        <span className={`text-xs font-medium ${config.color}`}>
          Fraud Score: {(fraudScore * 100).toFixed(0)}%
        </span>
      </div>
    );
  }

  return (
    <div className={`p-4 rounded-card border ${config.borderColor} ${config.bgColor}`}>
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-lg ${config.bgColor} border ${config.borderColor}`}>
          <Icon size={24} className={config.color} />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h4 className={`text-sm font-semibold ${config.color}`}>
              {config.label}
            </h4>
            <span className="text-xs text-user-muted">
              Score: {(fraudScore * 100).toFixed(1)}%
            </span>
          </div>
          <p className="text-xs text-user-muted mb-3">
            {config.message}
          </p>

          {fraudDetails?.checks && fraudDetails.checks.length > 0 && (
            <div className="space-y-2">
              {fraudDetails.checks.map((check, index) => (
                <div key={index} className="flex items-center justify-between text-xs">
                  <span className="text-user-text">{check.name}</span>
                  <div className="flex items-center gap-2">
                    {check.score !== undefined && (
                      <span className="text-user-muted font-data">
                        {(check.score * 100).toFixed(0)}%
                      </span>
                    )}
                    {check.passed ? (
                      <ShieldCheck size={14} className="text-risk-low" />
                    ) : (
                      <AlertTriangle size={14} className="text-risk-very_high" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {!fraudCheckPassed && (
            <div className="mt-3 pt-3 border-t border-current opacity-50">
              <p className="text-xs text-user-text">
                <strong>Next steps:</strong> Your application will be reviewed by our risk team within 24 hours.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FraudCheckStatus;
