import React from 'react';
import { AlertTriangle, CheckCircle, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

interface FairnessMetrics {
  disparateImpactRatio: Record<string, number>;
  demographicParity: Record<string, number>;
  equalOpportunity: Record<string, number>;
  subgroupAUC: Array<{ group: string; auc: number }>;
  biasFlags: Array<{ group: string; metric: string; severity: 'low' | 'medium' | 'high' }>;
  approvalRatesByGroup: Array<{ group: string; rate: number }>;
}

interface FairnessMonitorProps {
  metrics: FairnessMetrics;
}

const FairnessMonitor: React.FC<FairnessMonitorProps> = ({ metrics }) => {
  const getDIRStatus = (dir: number) => {
    if (dir >= 0.8 && dir <= 1.25) {
      return { label: 'PASS', color: 'text-risk-low', bgColor: 'bg-green-50', icon: CheckCircle };
    }
    if (dir >= 0.7 && dir < 0.8) {
      return { label: 'WARNING', color: 'text-risk-medium', bgColor: 'bg-yellow-50', icon: AlertTriangle };
    }
    return { label: 'FAIL', color: 'text-risk-very_high', bgColor: 'bg-red-50', icon: AlertTriangle };
  };

  const getSeverityColor = (severity: string) => {
    if (severity === 'low') return 'bg-green-100 text-risk-low';
    if (severity === 'medium') return 'bg-yellow-100 text-risk-medium';
    return 'bg-red-100 text-risk-very_high';
  };

  return (
    <div className="space-y-6">
      {/* Disparate Impact Ratio Cards */}
      <div>
        <h3 className="text-sm font-semibold text-user-text mb-3">
          Disparate Impact Ratio (DIR) by Protected Group
        </h3>
        <p className="text-xs text-user-muted mb-4">
          DIR should be between 0.8 and 1.25 to pass fairness threshold (80% rule)
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(metrics.disparateImpactRatio).map(([group, dir]) => {
            const status = getDIRStatus(dir);
            const Icon = status.icon;
            return (
              <div
                key={group}
                className={`border rounded-card p-4 ${status.bgColor} border-current`}
              >
                <div className="flex items-start justify-between mb-2">
                  <p className="text-sm font-medium text-user-text">
                    {group.replace(/_/g, ' ').toUpperCase()}
                  </p>
                  <Icon size={18} className={status.color} />
                </div>
                <p className={`text-2xl font-bold font-data mb-1 ${status.color}`}>
                  {dir.toFixed(3)}
                </p>
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-medium ${status.color}`}>
                    {status.label}
                  </span>
                  <span className="text-xs text-user-muted">
                    {dir >= 0.8 && dir <= 1.25 ? '✓ Compliant' : '⚠ Review Required'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Bias Flags */}
      {metrics.biasFlags.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-user-text mb-3 flex items-center gap-2">
            <AlertTriangle size={16} className="text-risk-medium" />
            Active Bias Flags
          </h3>
          <div className="space-y-2">
            {metrics.biasFlags.map((flag, index) => (
              <div
                key={index}
                className="bg-white border border-user-border rounded-card p-3 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-1 rounded-pill text-xs font-medium ${getSeverityColor(flag.severity)}`}>
                    {flag.severity.toUpperCase()}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-user-text">
                      {flag.group.replace(/_/g, ' ')}
                    </p>
                    <p className="text-xs text-user-muted">
                      {flag.metric}
                    </p>
                  </div>
                </div>
                <button className="text-xs text-barclays-blue hover:underline">
                  Investigate
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Approval Rates by Group */}
        <div className="bg-white border border-user-border rounded-card p-4">
          <h3 className="text-sm font-semibold text-user-text mb-4">
            Approval Rates by Protected Group
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={metrics.approvalRatesByGroup}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="group" tick={{ fontSize: 11 }} angle={-45} textAnchor="end" height={80} />
              <YAxis tick={{ fontSize: 12 }} domain={[0, 100]} />
              <Tooltip />
              <Bar dataKey="rate" fill="#00AEEF" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Subgroup AUC */}
        <div className="bg-white border border-user-border rounded-card p-4">
          <h3 className="text-sm font-semibold text-user-text mb-4">
            Model Performance by Subgroup (AUC)
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={metrics.subgroupAUC} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 12 }} />
              <YAxis dataKey="group" type="category" tick={{ fontSize: 11 }} width={100} />
              <Tooltip />
              <Bar dataKey="auc" fill="#10B981" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <p className="text-xs text-user-muted mt-2">
            AUC &gt; 0.7 indicates good model performance for the subgroup
          </p>
        </div>
      </div>

      {/* Fairness Metrics Table */}
      <div className="bg-white border border-user-border rounded-card p-4">
        <h3 className="text-sm font-semibold text-user-text mb-4">
          Detailed Fairness Metrics
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-user-border">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-semibold text-user-text">
                  Protected Group
                </th>
                <th className="px-4 py-2 text-center text-xs font-semibold text-user-text">
                  DIR
                </th>
                <th className="px-4 py-2 text-center text-xs font-semibold text-user-text">
                  Demographic Parity
                </th>
                <th className="px-4 py-2 text-center text-xs font-semibold text-user-text">
                  Equal Opportunity
                </th>
                <th className="px-4 py-2 text-center text-xs font-semibold text-user-text">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {Object.keys(metrics.disparateImpactRatio).map((group) => {
                const dir = metrics.disparateImpactRatio[group];
                const dp = metrics.demographicParity[group] || 0;
                const eo = metrics.equalOpportunity[group] || 0;
                const status = getDIRStatus(dir);
                return (
                  <tr key={group} className="border-b border-user-border hover:bg-gray-50">
                    <td className="px-4 py-3 text-user-text">
                      {group.replace(/_/g, ' ')}
                    </td>
                    <td className="px-4 py-3 text-center font-data text-user-text">
                      {dir.toFixed(3)}
                    </td>
                    <td className="px-4 py-3 text-center font-data text-user-text">
                      {dp.toFixed(3)}
                    </td>
                    <td className="px-4 py-3 text-center font-data text-user-text">
                      {eo.toFixed(3)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`px-2 py-1 rounded-pill text-xs font-medium ${status.bgColor} ${status.color}`}>
                        {status.label}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Compliance Summary */}
      <div className="bg-barclays-lightblue border border-barclays-blue rounded-card p-4">
        <h3 className="text-sm font-semibold text-barclays-navy mb-2">
          Fairness Compliance Summary
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-user-muted mb-1">Groups Passing DIR</p>
            <p className="text-xl font-bold text-barclays-navy font-data">
              {Object.values(metrics.disparateImpactRatio).filter(d => d >= 0.8 && d <= 1.25).length} / {Object.keys(metrics.disparateImpactRatio).length}
            </p>
          </div>
          <div>
            <p className="text-user-muted mb-1">Active Bias Flags</p>
            <p className="text-xl font-bold text-barclays-navy font-data">
              {metrics.biasFlags.length}
            </p>
          </div>
          <div>
            <p className="text-user-muted mb-1">Overall Status</p>
            <p className={`text-xl font-bold font-data ${metrics.biasFlags.filter(f => f.severity === 'high').length > 0 ? 'text-risk-very_high' : 'text-risk-low'}`}>
              {metrics.biasFlags.filter(f => f.severity === 'high').length > 0 ? 'REVIEW REQUIRED' : 'COMPLIANT'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FairnessMonitor;
