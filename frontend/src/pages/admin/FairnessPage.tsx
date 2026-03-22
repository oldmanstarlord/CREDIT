import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store/store';
import { fetchFairnessReport } from '../../store/adminSlice';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, CartesianGrid, Cell } from 'recharts';
import { Scale, CheckCircle, AlertTriangle } from 'lucide-react';

const FairnessPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { fairnessReport: report, loading, error } = useSelector((s: RootState) => s.admin);

  useEffect(() => { dispatch(fetchFairnessReport(30)); }, [dispatch]);

  if (loading && !report) {
    return <div className="text-admin-muted font-body">Loading fairness report...</div>;
  }

  if (error || !report || report.error) {
    return (
      <div className="p-4 bg-admin-surface border border-admin-border rounded-card text-sm text-admin-muted font-body">
        {typeof error === 'string' ? error : report?.error || 'Fairness report is currently unavailable.'}
      </div>
    );
  }

  const ratios = report.disparate_impact_by_category?.ratios || {};
  const flags = report.disparate_impact_by_category?.flags || [];
  const diData = Object.entries(ratios).map(([pair, value]) => ({
    group: String(pair).replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase()),
    impact: Number(value),
    pass: Number(value) >= 0.8,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Scale size={22} className="text-admin-accent" />
          <h1 className="text-2xl font-display font-bold text-admin-text">Model Fairness Monitor</h1>
        </div>
        <span className="text-xs text-admin-muted font-body">
          Analysed: {Number(report.total_applications || 0).toLocaleString()} applications (last {report.time_window_days} days)
        </span>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-admin-surface border border-admin-border rounded-card p-5">
          <h3 className="text-xs text-admin-muted font-body mb-2">4/5ths Rule Compliance</h3>
          <div className="flex items-center gap-2">
            {flags.length === 0 ? (
              <><CheckCircle size={20} className="text-risk-low" /><span className="text-lg font-display font-bold text-risk-low">ALL PASS</span></>
            ) : (
              <><AlertTriangle size={20} className="text-risk-medium" /><span className="text-lg font-display font-bold text-risk-medium">{flags.length} VIOLATIONS</span></>
            )}
          </div>
          <p className="text-xs text-admin-muted mt-2 font-body">Disparate impact ratio must be ≥ 0.8</p>
        </div>
        <div className="bg-admin-surface border border-admin-border rounded-card p-5">
          <h3 className="text-xs text-admin-muted font-body mb-2">Equalized Odds Metric</h3>
          <p className={`text-2xl font-display font-bold ${Number(report.model_metrics?.avg_probability_of_default || 0) <= 0.3 ? 'text-risk-low' : 'text-risk-medium'}`}>
            {Number(report.model_metrics?.avg_probability_of_default || 0).toFixed(2)}
          </p>
          <p className="text-xs text-admin-muted mt-2 font-body">Portfolio average probability of default</p>
        </div>
        <div className="bg-admin-surface border border-admin-border rounded-card p-5">
          <h3 className="text-xs text-admin-muted font-body mb-2">Model AUC (Overall)</h3>
          <p className="text-2xl font-display font-bold text-admin-accent">
            {Number(report.model_metrics?.avg_credit_score || 0).toFixed(0)}
          </p>
          <p className="text-xs text-admin-muted mt-2 font-body">Average credit score in fairness window</p>
        </div>
      </div>

      {/* Disparate Impact Chart */}
      <div className="bg-admin-surface border border-admin-border rounded-card p-5">
        <h3 className="text-sm font-semibold text-admin-text mb-4 font-body">Disparate Impact by Category</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={diData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#1E2D45" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 10, fill: '#64748B' }} domain={[0, 1.2]} />
            <YAxis dataKey="group" type="category" width={140} tick={{ fontSize: 11, fill: '#F1F5F9' }} />
            <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #1E2D45', borderRadius: '8px', fontSize: '12px', color: '#F1F5F9' }} />
            <ReferenceLine x={0.8} stroke="#EF4444" strokeDasharray="4 4" label={{ value: '4/5ths threshold', fill: '#EF4444', fontSize: 10, position: 'top' }} />
            <Bar dataKey="impact" fill="#00AEEF" radius={[0, 6, 6, 0]} barSize={24}>
              {diData.map((entry: any, index: number) => (
                <Cell key={index} fill={entry.pass ? '#10B981' : '#F59E0B'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Bias Flags Table */}
      <div className="bg-admin-surface border border-admin-border rounded-card overflow-hidden">
        <div className="px-5 py-4 border-b border-admin-border">
          <h3 className="text-sm font-semibold text-admin-text font-body">Disparate Impact Flags</h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-admin-border">
              {['Pair', 'DIR', 'Gap', 'Severity'].map((h) => (
                <th key={h} className="px-5 py-3 text-left text-[11px] font-semibold text-admin-muted uppercase tracking-wider font-body">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {flags.length === 0 && (
              <tr>
                <td className="px-5 py-3 text-sm text-admin-muted font-body" colSpan={4}>No bias flags detected.</td>
              </tr>
            )}
            {flags.map((flag: any) => (
              <tr key={flag.pair} className="border-b border-admin-border/50 hover:bg-admin-surface2 transition-colors">
                <td className="px-5 py-3 text-sm text-admin-text capitalize font-body">{String(flag.pair).replace(/_/g, ' ')}</td>
                <td className="px-5 py-3 text-sm font-data font-medium text-admin-accent">{Number(flag.dir).toFixed(3)}</td>
                <td className="px-5 py-3 text-sm font-data text-admin-muted">{Number(flag.approval_gap).toFixed(3)}</td>
                <td className="px-5 py-3">
                  <span className={`px-2 py-1 text-[10px] rounded-pill font-medium ${String(flag.severity) === 'HIGH' ? 'bg-risk-very_high/20 text-risk-very_high' : 'bg-risk-medium/20 text-risk-medium'}`}>
                    {String(flag.severity)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
export default FairnessPage;
