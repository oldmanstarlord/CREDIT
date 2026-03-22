import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store/store';
import { fetchKPIs } from '../../store/adminSlice';
import { FileStack, CheckCircle, TrendingUp, AlertTriangle } from 'lucide-react';

const DashboardPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { kpis, loading, error } = useSelector((s: RootState) => s.admin);

  useEffect(() => {
    dispatch(fetchKPIs(30));
  }, [dispatch]);

  if (loading && !kpis) {
    return <div className="text-admin-muted font-body">Loading dashboard...</div>;
  }

  if (error || !kpis) {
    return (
      <div className="p-4 bg-admin-surface border border-admin-border rounded-card text-sm text-admin-muted font-body">
        {typeof error === 'string' ? error : 'Dashboard data is currently unavailable.'}
      </div>
    );
  }

  const kpiCards = [
    { label: 'Total Applications', value: kpis.total_applications.toLocaleString(), icon: FileStack, color: 'bg-admin-accent/20 text-admin-accent' },
    { label: 'Approval Rate', value: `${kpis.decisions.approval_rate_pct}%`, icon: CheckCircle, color: 'bg-risk-low/20 text-risk-low' },
    { label: 'Avg Credit Score', value: Math.round(kpis.model_metrics.avg_credit_score).toString(), icon: TrendingUp, color: 'bg-risk-medium/20 text-risk-medium' },
    { label: 'Portfolio at Risk', value: `${(kpis.model_metrics.avg_probability_of_default * 100).toFixed(1)}%`, icon: AlertTriangle, color: `${kpis.model_metrics.avg_probability_of_default > 0.2 ? 'bg-risk-very_high/20 text-risk-very_high' : 'bg-risk-medium/20 text-risk-medium'}` },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-display font-bold text-admin-text">Dashboard</h1>
        <div className="flex gap-2">
          {['Today', 'Week', 'Month'].map((p) => (
            <button key={p} className="px-3 py-1.5 text-xs font-medium text-admin-muted bg-admin-surface rounded-pill border border-admin-border hover:text-admin-text hover:border-admin-accent transition-colors">
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {kpiCards.map((kpi) => (
          <div key={kpi.label} className="bg-admin-surface border border-admin-border rounded-card p-5">
            <div className="flex items-center justify-between mb-3">
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${kpi.color}`}>
                <kpi.icon size={18} />
              </div>
            </div>
            <p className="text-3xl font-display font-bold text-admin-text">{kpi.value}</p>
            <div className="flex items-center justify-between mt-2">
              <span className="text-xs text-admin-muted font-body">{kpi.label}</span>
              <span className="text-xs font-data font-medium text-admin-muted">Live</span>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-admin-surface border border-admin-border rounded-card p-5">
        <h3 className="text-sm font-semibold text-admin-text mb-3 font-body">Operational Summary</h3>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-display font-bold text-admin-text">{kpis.decisions.approved}</p>
            <p className="text-xs text-admin-muted font-body mt-1">Approved</p>
          </div>
          <div>
            <p className="text-2xl font-display font-bold text-admin-text">{kpis.decisions.held}</p>
            <p className="text-xs text-admin-muted font-body mt-1">On Hold</p>
          </div>
          <div>
            <p className="text-2xl font-display font-bold text-admin-text">{kpis.decisions.rejected}</p>
            <p className="text-xs text-admin-muted font-body mt-1">Rejected</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
