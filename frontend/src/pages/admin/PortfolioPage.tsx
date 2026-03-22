import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store/store';
import { fetchPortfolioRisk } from '../../store/adminSlice';
import { Briefcase, TrendingUp, AlertTriangle } from 'lucide-react';

const PortfolioPage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { portfolioRisk, loading, error } = useSelector((s: RootState) => s.admin);

  useEffect(() => { dispatch(fetchPortfolioRisk()); }, [dispatch]);

  if (loading && !portfolioRisk) {
    return <div className="text-admin-muted font-body">Loading portfolio risk...</div>;
  }

  if (error || !portfolioRisk || portfolioRisk.error) {
    return (
      <div className="p-4 bg-admin-surface border border-admin-border rounded-card text-sm text-admin-muted font-body">
        {typeof error === 'string' ? error : portfolioRisk?.error || 'Portfolio risk data is unavailable.'}
      </div>
    );
  }

  const simulation = portfolioRisk.simulation_results || {};
  const stats = portfolioRisk.portfolio_statistics || {};
  const concentration = portfolioRisk.concentration_risk || {};
  const categoryRows = Object.entries(stats.by_category || {}).map(([category, value]: [string, any]) => ({
    category,
    exposure: Number(value.pct_of_portfolio || 0),
    el: Number(value.avg_pd || 0) * 100,
    count: Number(value.count || 0),
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Briefcase size={22} className="text-admin-accent" />
          <h1 className="text-2xl font-display font-bold text-admin-text">Portfolio Risk</h1>
        </div>
        <span className="text-xs text-admin-muted font-body">Monte Carlo simulations: {simulation.n_simulations || 0}</span>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {[
          { label: 'Total Exposure', value: `₹${(Number(stats.total_exposure_inr || 0) / 10000000).toFixed(1)}Cr`, icon: Briefcase, color: 'text-admin-accent' },
          { label: 'Expected Loss', value: `${Number(simulation.expected_loss_pct || 0).toFixed(2)}%`, icon: TrendingUp, color: Number(simulation.expected_loss_pct || 0) < 5 ? 'text-risk-low' : 'text-risk-medium' },
          { label: 'VaR (95%)', value: `₹${(Number(simulation.var_95_inr || 0) / 100000).toFixed(0)}L`, icon: AlertTriangle, color: 'text-risk-medium' },
          { label: 'VaR (99%)', value: `₹${(Number(simulation.var_99_inr || 0) / 100000).toFixed(0)}L`, icon: AlertTriangle, color: 'text-risk-very_high' },
        ].map((card) => (
          <div key={card.label} className="bg-admin-surface border border-admin-border rounded-card p-5">
            <div className="flex items-center gap-2 mb-2">
              <card.icon size={16} className={card.color} />
              <span className="text-xs text-admin-muted font-body">{card.label}</span>
            </div>
            <p className={`text-2xl font-display font-bold ${card.color}`}>{card.value}</p>
          </div>
        ))}
      </div>

      <div className="bg-admin-surface border border-admin-border rounded-card overflow-hidden">
        <div className="px-5 py-4 border-b border-admin-border">
          <h3 className="text-sm font-semibold text-admin-text font-body">Risk by Category</h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-admin-border">
              {['Category', 'Loans', 'Exposure %', 'Avg PD %'].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-admin-muted uppercase tracking-wider font-body">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {categoryRows.map((cr) => (
              <tr key={cr.category} className="border-b border-admin-border/50 hover:bg-admin-surface2 transition-colors">
                <td className="px-4 py-3 text-sm text-admin-text font-body">{cr.category.replace(/_/g, ' ')}</td>
                <td className="px-4 py-3 text-sm font-data text-admin-muted">{cr.count}</td>
                <td className="px-4 py-3 text-sm font-data text-admin-accent">{cr.exposure.toFixed(1)}%</td>
                <td className="px-4 py-3 text-sm font-data text-admin-muted">{cr.el.toFixed(2)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-admin-surface border border-admin-border rounded-card p-5">
        <h3 className="text-sm font-semibold text-admin-text mb-4 font-body">Concentration Risk</h3>
        <p className="text-sm text-admin-muted font-body">
          Risk Level: <span className="text-admin-text font-semibold">{concentration.risk_assessment || 'UNKNOWN'}</span>
        </p>
        {Array.isArray(concentration.recommendations) && concentration.recommendations.length > 0 && (
          <ul className="mt-2 space-y-1 text-sm text-admin-muted font-body list-disc pl-5">
            {concentration.recommendations.map((r: string) => <li key={r}>{r}</li>)}
          </ul>
        )}
      </div>
    </div>
  );
};

export default PortfolioPage;
