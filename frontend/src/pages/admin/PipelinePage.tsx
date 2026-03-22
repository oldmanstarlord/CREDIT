import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store/store';
import { fetchApplications, fetchApplicationDetail, closeDetailPanel, setFilters } from '../../store/adminSlice';
import { adminService } from '../../services/adminService';
import { LayoutGrid, List, Search, ChevronLeft, ChevronRight, X, MoreVertical } from 'lucide-react';
import CreditScoreGauge from '../../components/CreditScoreGauge';
import ShapChart from '../../components/ShapChart';

const statusColors: Record<string, string> = {
  pre_screening: 'bg-decision-pending/20 text-decision-pending',
  ml_scored: 'bg-admin-accent/20 text-admin-accent',
  hold: 'bg-decision-hold/20 text-decision-hold',
  approved: 'bg-decision-approve/20 text-decision-approve',
  rejected: 'bg-decision-reject/20 text-decision-reject',
  policy_checked: 'bg-admin-accent/20 text-admin-accent',
};

const riskColor = (score: number | null) => {
  if (!score) return 'text-admin-muted';
  if (score >= 750) return 'text-risk-low';
  if (score >= 650) return 'text-risk-medium';
  if (score >= 550) return 'text-risk-high';
  return 'text-risk-very_high';
};

const pdColor = (pd: number | null) => {
  if (!pd) return 'text-admin-muted';
  if (pd < 0.15) return 'text-risk-low';
  if (pd < 0.4) return 'text-risk-medium';
  return 'text-risk-very_high';
};

const timeAgo = (dateStr: string) => {
  const diff = Date.now() - new Date(dateStr).getTime();
  const hrs = Math.floor(diff / 3600000);
  if (hrs < 1) return `${Math.floor(diff / 60000)}m ago`;
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
};

const PipelinePage: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { applications, totalApplications, selectedApplication, detailPanelOpen, filters, loading, error } = useSelector((s: RootState) => s.admin);
  const [viewMode, setViewMode] = useState<'table' | 'kanban'>('table');
  const [searchQuery, setSearchQuery] = useState('');
  const [decisionModal, setDecisionModal] = useState<{ type: string; appId: string } | null>(null);
  const [decisionReason, setDecisionReason] = useState('');
  const [overrideJustification, setOverrideJustification] = useState('');

  const displayApps = applications;

  useEffect(() => {
    dispatch(fetchApplications(filters));
  }, [dispatch, filters]);

  const openDetail = (id: string) => {
    dispatch(fetchApplicationDetail(id));
  };

  const makeDecision = async (appId: string, decision: string, reason: string) => {
    try {
      await adminService.makeDecision(appId, { decision, reason });
      dispatch(fetchApplications(filters));
      setDecisionModal(null);
      setDecisionReason('');
    } catch {}
  };

  const submitOverride = async (appId: string, decision: string) => {
    try {
      await adminService.overrideDecision(appId, { override_decision: decision, justification: overrideJustification });
      dispatch(fetchApplications(filters));
      setDecisionModal(null);
      setOverrideJustification('');
    } catch {}
  };

  // -- Kanban columns --
  const kanbanColumns = [
    { key: 'pre_screening', label: 'Pre-Screening', color: 'border-decision-pending' },
    { key: 'ml_scored', label: 'ML Scoring', color: 'border-admin-accent' },
    { key: 'hold', label: 'On Hold', color: 'border-decision-hold' },
    { key: 'decided', label: 'Decided', color: 'border-decision-approve' },
  ];

  const getKanbanApps = (col: string) => {
    if (col === 'decided') return displayApps.filter((a) => a.final_decision === 'approved' || a.final_decision === 'rejected');
    return displayApps.filter((a) => a.status === col || (col === 'hold' && a.final_decision === 'hold'));
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-display font-bold text-admin-text">Applications</h1>
        <div className="flex items-center gap-2">
          <button onClick={() => setViewMode('kanban')}
            className={`p-2 rounded-lg transition-colors ${viewMode === 'kanban' ? 'bg-admin-accent/20 text-admin-accent' : 'text-admin-muted hover:text-admin-text'}`}>
            <LayoutGrid size={18} />
          </button>
          <button onClick={() => setViewMode('table')}
            className={`p-2 rounded-lg transition-colors ${viewMode === 'table' ? 'bg-admin-accent/20 text-admin-accent' : 'text-admin-muted hover:text-admin-text'}`}>
            <List size={18} />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-admin-muted" />
          <input type="text" placeholder="Search by name or ID..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-admin-surface border border-admin-border rounded-lg text-sm text-admin-text font-body focus:outline-none focus:border-admin-accent" />
        </div>
        {['Category', 'Status', 'Risk Band'].map((label) => (
          <select key={label} className="px-3 py-2 bg-admin-surface border border-admin-border rounded-lg text-xs text-admin-muted font-body focus:outline-none focus:border-admin-accent">
            <option>{label} ▼</option>
          </select>
        ))}
      </div>

      {/* KANBAN VIEW */}
      {viewMode === 'kanban' && (
        <>
        {loading && <div className="text-admin-muted text-sm font-body">Loading applications...</div>}
        {error && <div className="text-risk-very_high text-sm font-body">{error}</div>}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {kanbanColumns.map((col) => {
            const colApps = getKanbanApps(col.key);
            return (
              <div key={col.key} className="space-y-2">
                <div className={`flex items-center gap-2 pb-2 border-b-2 ${col.color}`}>
                  <h3 className="text-sm font-semibold text-admin-text font-body">{col.label}</h3>
                  <span className="px-2 py-0.5 text-[10px] font-data bg-admin-surface2 text-admin-muted rounded-pill">{colApps.length}</span>
                </div>
                <div className="space-y-2 max-h-[60vh] overflow-y-auto">
                  {colApps.map((app) => (
                    <button key={app.id} onClick={() => openDetail(app.id)}
                      className="w-full text-left bg-admin-surface border border-admin-border rounded-card p-4 hover:border-admin-accent transition-all hover:-translate-y-0.5">
                      <div className="flex items-start justify-between">
                        <span className="font-medium text-sm text-admin-text font-body">{app.user_name}</span>
                        <span className={`px-2 py-0.5 text-[10px] rounded-pill font-medium ${statusColors[app.status] || 'bg-admin-surface2 text-admin-muted'}`}>
                          {app.status?.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-2 text-xs text-admin-muted font-body">
                        <span className="capitalize">{app.category?.replace(/_/g, ' ')}</span>
                        <span>•</span>
                        <span>₹{(app.requested_amount).toLocaleString()}</span>
                      </div>
                      <div className="flex items-center justify-between mt-3">
                        <span className={`text-sm font-data font-medium ${riskColor(app.credit_score)}`}>{app.credit_score || '—'}</span>
                        <span className="text-[10px] text-admin-muted font-body">{timeAgo(app.created_at)}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
        </>
      )}

      {/* TABLE VIEW */}
      {viewMode === 'table' && (
        <div className="bg-admin-surface border border-admin-border rounded-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-admin-border">
                  {['ID', 'Name', 'Category', 'Score', 'PD%', 'Amount', 'Status', 'Time', ''].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-admin-muted uppercase tracking-wider font-body">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {!loading && displayApps.length === 0 && (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-admin-muted text-sm font-body">
                      No applications found for the selected filters.
                    </td>
                  </tr>
                )}
                {displayApps.map((app) => (
                  <tr key={app.id} className="border-b border-admin-border/50 hover:bg-admin-surface2 transition-colors cursor-pointer" onClick={() => openDetail(app.id)}>
                    <td className="px-4 py-3 text-xs font-data text-admin-muted">{app.application_number}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-admin-accent/20 flex items-center justify-center text-[10px] font-semibold text-admin-accent">
                          {app.user_name?.split(' ').map((n) => n[0]).join('')}
                        </div>
                        <span className="text-sm text-admin-text font-body font-medium">{app.user_name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-admin-muted capitalize font-body">{app.category?.replace(/_/g, ' ')}</td>
                    <td className="px-4 py-3">
                      <span className={`text-sm font-data font-medium ${riskColor(app.credit_score)}`}>{app.credit_score || '—'}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-sm font-data ${pdColor(app.probability_of_default)}`}>
                        {app.probability_of_default ? `${(app.probability_of_default * 100).toFixed(1)}%` : '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-admin-text font-data text-right">₹{app.requested_amount.toLocaleString()}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-[10px] rounded-pill font-medium ${statusColors[app.status] || 'bg-admin-surface2 text-admin-muted'}`}>
                        {app.status?.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-admin-muted font-body">{timeAgo(app.created_at)}</td>
                    <td className="px-4 py-3">
                      <button className="p-1 text-admin-muted hover:text-admin-text"><MoreVertical size={14} /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-3 border-t border-admin-border">
            <span className="text-xs text-admin-muted font-body">Showing 1-{displayApps.length} of {totalApplications || displayApps.length}</span>
            <div className="flex items-center gap-1">
              <button className="p-1.5 text-admin-muted hover:text-admin-text rounded hover:bg-admin-surface2"><ChevronLeft size={14} /></button>
              {[1, 2, 3].map((p) => (
                <button key={p} className={`w-7 h-7 text-xs rounded ${p === 1 ? 'bg-admin-accent text-white' : 'text-admin-muted hover:bg-admin-surface2'}`}>{p}</button>
              ))}
              <button className="p-1.5 text-admin-muted hover:text-admin-text rounded hover:bg-admin-surface2"><ChevronRight size={14} /></button>
            </div>
          </div>
        </div>
      )}

      {/* DETAIL PANEL */}
      {detailPanelOpen && (
        <>
          <div className="fixed inset-0 bg-black/50 z-40" onClick={() => dispatch(closeDetailPanel())} />
          <div className="fixed right-0 top-0 h-full w-full md:w-[600px] bg-admin-bg border-l border-admin-border z-50 overflow-y-auto animate-slide-up">
            <div className="sticky top-0 bg-admin-bg border-b border-admin-border px-6 py-4 flex items-center justify-between z-10">
              <div>
                <h2 className="text-lg font-display font-semibold text-admin-text">
                  {selectedApplication?.application_number || 'Application'}
                </h2>
                <p className="text-xs text-admin-muted font-body">{selectedApplication?.user?.name || 'Details'}</p>
              </div>
              <button onClick={() => dispatch(closeDetailPanel())} className="p-2 text-admin-muted hover:text-admin-text hover:bg-admin-surface2 rounded-lg">
                <X size={18} />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Identity */}
              <div className="bg-admin-surface border border-admin-border rounded-card p-4">
                <h3 className="text-sm font-semibold text-admin-text mb-3 font-body">Applicant Identity</h3>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div><span className="text-admin-muted">Name:</span> <span className="text-admin-text font-medium">{selectedApplication?.user?.name || '-'}</span></div>
                  <div><span className="text-admin-muted">Phone:</span> <span className="text-admin-text font-data">{selectedApplication?.user?.phone || '-'}</span></div>
                  <div><span className="text-admin-muted">Email:</span> <span className="text-admin-text font-data">{selectedApplication?.user?.email || '-'}</span></div>
                  <div><span className="text-admin-muted">Category:</span> <span className="text-admin-text capitalize">{selectedApplication?.category?.replace(/_/g, ' ') || '-'}</span></div>
                </div>
              </div>

              {/* ML Scoring */}
              <div className="bg-admin-surface border border-admin-border rounded-card p-4">
                <h3 className="text-sm font-semibold text-admin-text mb-3 font-body">ML Scoring</h3>
                <div className="flex items-center gap-6">
                  <CreditScoreGauge score={selectedApplication?.ml_scoring?.credit_score || 0} size={160} animated={false} />
                  <div className="space-y-2">
                    <div>
                      <span className="text-xs text-admin-muted font-body">PD Score</span>
                      <p className="text-xl font-data font-bold text-admin-accent">
                        {(((selectedApplication?.ml_scoring?.probability_of_default || 0)) * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <span className="text-xs text-admin-muted font-body">Risk Band</span>
                      <p className="text-sm text-admin-text capitalize font-body">{selectedApplication?.ml_scoring?.risk_band || '-'}</p>
                    </div>
                  </div>
                </div>
                {selectedApplication?.ml_scoring?.shap_explanation && (
                  <div className="mt-4">
                    <ShapChart
                      positiveFactors={(selectedApplication.ml_scoring.shap_explanation.top_positive_factors || []).map((f: any) => ({ feature: f.feature || f, value: f.value || 0.08 }))}
                      negativeFactors={(selectedApplication.ml_scoring.shap_explanation.top_negative_factors || []).map((f: any) => ({ feature: f.feature || f, value: f.value || 0.06 }))}
                      compact
                    />
                    {selectedApplication.ml_scoring.shap_explanation.plain_english_summary && (
                      <div className="mt-3 p-3 border-l-2 border-admin-accent bg-admin-surface2/50 rounded-r-lg">
                        <p className="text-xs text-admin-muted font-body italic">{selectedApplication.ml_scoring.shap_explanation.plain_english_summary}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Decision Panel */}
              <div className="bg-admin-surface border border-admin-border rounded-card p-4">
                <h3 className="text-sm font-semibold text-admin-text mb-4 font-body">Decision</h3>
                <div className="flex gap-2">
                  {[
                    { label: '✓ APPROVE', decision: 'approved', className: 'bg-decision-approve hover:shadow-approve text-white' },
                    { label: '⏸ HOLD', decision: 'hold', className: 'bg-decision-hold hover:shadow-md text-white' },
                    { label: '✗ REJECT', decision: 'rejected', className: 'bg-decision-reject hover:shadow-reject text-white' },
                  ].map((btn) => (
                    <button key={btn.decision} onClick={() => setDecisionModal({ type: btn.decision, appId: selectedApplication?.id || '' })}
                      className={`flex-1 py-3 rounded-lg font-semibold text-sm transition-all ${btn.className}`}>
                      {btn.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Audit Trail */}
              <div className="bg-admin-surface border border-admin-border rounded-card p-4">
                <h3 className="text-sm font-semibold text-admin-text mb-3 font-body">Audit Trail</h3>
                <div className="space-y-3">
                  {(selectedApplication?.audit_trail || [
                    { event_id: '1', event_type: 'application_submit', timestamp: new Date().toISOString(), actor_id: null },
                    { event_id: '2', event_type: 'pre_screening_pass', timestamp: new Date().toISOString(), actor_id: null },
                    { event_id: '3', event_type: 'ml_scoring_complete', timestamp: new Date().toISOString(), actor_id: null },
                  ]).map((event: any) => (
                    <div key={event.event_id} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div className={`w-2.5 h-2.5 rounded-full ${
                          event.event_type.includes('approve') ? 'bg-risk-low' :
                          event.event_type.includes('reject') ? 'bg-risk-very_high' :
                          event.event_type.includes('override') ? 'bg-risk-very_high' :
                          'bg-admin-accent'
                        }`} />
                        <div className="w-px flex-1 bg-admin-border" />
                      </div>
                      <div className="pb-3">
                        <p className="text-xs text-admin-text font-body">{event.event_type?.replace(/_/g, ' ')}</p>
                        <p className="text-[10px] text-admin-muted font-data">{new Date(event.timestamp).toLocaleString()}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Decision Modal */}
      {decisionModal && (
        <div className="fixed inset-0 bg-black/60 z-[60] flex items-end md:items-center justify-center">
          <div className="bg-admin-surface border border-admin-border rounded-t-2xl md:rounded-card w-full max-w-md p-6">
            <h3 className="text-lg font-display font-semibold text-admin-text mb-4">
              Confirm {decisionModal.type === 'approved' ? 'Approval' : decisionModal.type === 'rejected' ? 'Rejection' : 'Hold'}
            </h3>
            {decisionModal.type === 'rejected' && (
              <div className="mb-4">
                <label className="text-xs text-admin-muted font-body block mb-1">Reason (required)</label>
                <select className="w-full p-2 bg-admin-bg border border-admin-border rounded-lg text-sm text-admin-text font-body"
                  onChange={(e) => setDecisionReason(e.target.value)}>
                  <option value="">Select reason...</option>
                  <option>Insufficient income</option>
                  <option>High probability of default</option>
                  <option>Incomplete documentation</option>
                  <option>Fraud indicators detected</option>
                  <option>Policy threshold not met</option>
                </select>
              </div>
            )}
            <textarea placeholder="Additional notes..." value={decisionModal.type === 'rejected' ? decisionReason : decisionReason}
              onChange={(e) => setDecisionReason(e.target.value)}
              className="w-full p-3 bg-admin-bg border border-admin-border rounded-lg text-sm text-admin-text font-body mb-4 resize-none h-24 focus:outline-none focus:border-admin-accent" />
            <div className="flex gap-2">
              <button onClick={() => setDecisionModal(null)} className="flex-1 py-2.5 text-sm text-admin-muted border border-admin-border rounded-lg hover:bg-admin-surface2">Cancel</button>
              <button onClick={() => makeDecision(decisionModal.appId, decisionModal.type, decisionReason || decisionModal.type)}
                className={`flex-1 py-2.5 text-sm font-semibold rounded-lg text-white ${
                  decisionModal.type === 'approved' ? 'bg-decision-approve' : decisionModal.type === 'rejected' ? 'bg-decision-reject' : 'bg-decision-hold'
                }`}>
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PipelinePage;
