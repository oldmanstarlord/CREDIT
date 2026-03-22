import React, { useEffect, useMemo, useState } from 'react';
import { ScrollText, Search, ChevronDown, ChevronRight, Clock, Shield, Bot, User } from 'lucide-react';
import { adminService, AdminApplication } from '../../services/adminService';

type AuditLogEntry = {
  event_id: string;
  event_type: string;
  timestamp: string;
  actor_id: string | null;
  input_snapshot?: Record<string, unknown> | null;
  model_output?: Record<string, unknown> | null;
  policy_results?: Record<string, unknown> | null;
  decision_reason?: string | null;
};

const eventIcons: Record<string, { icon: React.ReactNode; color: string }> = {
  application_submit: { icon: <ScrollText size={14} />, color: 'bg-admin-accent/20 text-admin-accent' },
  pre_screening_pass: { icon: <Shield size={14} />, color: 'bg-risk-low/20 text-risk-low' },
  fraud_check_complete: { icon: <Shield size={14} />, color: 'bg-risk-medium/20 text-risk-medium' },
  ml_scoring_complete: { icon: <Bot size={14} />, color: 'bg-admin-accent/20 text-admin-accent' },
  policy_check_complete: { icon: <Shield size={14} />, color: 'bg-risk-low/20 text-risk-low' },
  decision_approved: { icon: <Shield size={14} />, color: 'bg-decision-approve/20 text-decision-approve' },
  decision_rejected: { icon: <Shield size={14} />, color: 'bg-decision-reject/20 text-decision-reject' },
  decision_held: { icon: <Clock size={14} />, color: 'bg-decision-hold/20 text-decision-hold' },
  override_approved: { icon: <Shield size={14} />, color: 'bg-risk-very_high/20 text-risk-very_high' },
  appeal_submitted: { icon: <User size={14} />, color: 'bg-admin-gold/20 text-admin-gold' },
};

const AuditLogPage: React.FC = () => {
  const [applications, setApplications] = useState<AdminApplication[]>([]);
  const [selectedApplicationId, setSelectedApplicationId] = useState<string>('');
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loadingApps, setLoadingApps] = useState<boolean>(true);
  const [loadingLogs, setLoadingLogs] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchApplications = async () => {
      try {
        setLoadingApps(true);
        setError(null);
        const response = await adminService.getApplications({ limit: 100, offset: 0, sort_by: 'created_at', sort_order: 'desc' });
        const fetched = response.data?.applications || [];
        setApplications(fetched);
        if (fetched.length > 0) {
          setSelectedApplicationId(fetched[0].id);
        }
      } catch (e: any) {
        setError(e?.response?.data?.detail || 'Failed to load applications for audit logs.');
      } finally {
        setLoadingApps(false);
      }
    };

    fetchApplications();
  }, []);

  useEffect(() => {
    const fetchLogs = async () => {
      if (!selectedApplicationId) {
        setLogs([]);
        return;
      }

      try {
        setLoadingLogs(true);
        setError(null);
        const response = await adminService.getAuditLogs(selectedApplicationId, 200);
        setLogs(response.data?.logs || []);
      } catch (e: any) {
        setError(e?.response?.data?.detail || 'Failed to load audit logs.');
        setLogs([]);
      } finally {
        setLoadingLogs(false);
      }
    };

    fetchLogs();
  }, [selectedApplicationId]);

  const eventTypes = useMemo(() => {
    return Array.from(new Set(logs.map((l) => l.event_type))).sort();
  }, [logs]);

  const selectedApp = applications.find((a) => a.id === selectedApplicationId);

  const filteredLogs = logs.filter((log) => {
    if (filterType && log.event_type !== filterType) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const appNumber = selectedApp?.application_number?.toLowerCase() || '';
      if (!appNumber.includes(q) && !log.event_type.toLowerCase().includes(q)) return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ScrollText size={22} className="text-admin-accent" />
          <h1 className="text-2xl font-display font-bold text-admin-text">Audit Log</h1>
        </div>
        <span className="text-xs text-admin-muted font-body">Immutable event timeline</span>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <select
          value={selectedApplicationId}
          onChange={(e) => setSelectedApplicationId(e.target.value)}
          disabled={loadingApps || applications.length === 0}
          className="px-3 py-2 bg-admin-surface border border-admin-border rounded-lg text-xs text-admin-muted font-body focus:outline-none focus:border-admin-accent"
        >
          {applications.length === 0 ? (
            <option value="">No applications available</option>
          ) : (
            applications.map((app) => (
              <option key={app.id} value={app.id}>{app.application_number}</option>
            ))
          )}
        </select>
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-admin-muted" />
          <input type="text" placeholder="Search by application ID..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-admin-surface border border-admin-border rounded-lg text-sm text-admin-text font-body focus:outline-none focus:border-admin-accent" />
        </div>
        <select value={filterType} onChange={(e) => setFilterType(e.target.value)}
          className="px-3 py-2 bg-admin-surface border border-admin-border rounded-lg text-xs text-admin-muted font-body focus:outline-none focus:border-admin-accent">
          <option value="">All Events</option>
          {eventTypes.map((t) => (
            <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
          ))}
        </select>
      </div>

      {/* Timeline */}
      <div className="bg-admin-surface border border-admin-border rounded-card p-6">
        {error && <p className="text-sm text-admin-muted font-body mb-3">{error}</p>}
        {(loadingApps || loadingLogs) && <p className="text-sm text-admin-muted font-body mb-3">Loading audit logs...</p>}
        {!loadingLogs && filteredLogs.length === 0 && !error && (
          <p className="text-sm text-admin-muted font-body mb-3">No audit logs found for the selected application.</p>
        )}
        <div className="space-y-0">
          {filteredLogs.map((log, index) => {
            const ei = eventIcons[log.event_type] || { icon: <Clock size={14} />, color: 'bg-admin-surface2 text-admin-muted' };
            const isExpanded = expandedId === log.event_id;
            const details = {
              input_snapshot: log.input_snapshot,
              model_output: log.model_output,
              policy_results: log.policy_results,
              decision_reason: log.decision_reason,
            };
            const hasDetails = Object.values(details).some((v) => v !== null && v !== undefined);
            return (
              <div key={log.event_id} className="flex gap-4 group">
                {/* Timeline line */}
                <div className="flex flex-col items-center">
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center ${ei.color} shrink-0`}>
                    {ei.icon}
                  </div>
                  {index < filteredLogs.length - 1 && <div className="w-px flex-1 bg-admin-border min-h-[24px]" />}
                </div>

                {/* Content */}
                <div className="flex-1 pb-5">
                  <button onClick={() => setExpandedId(isExpanded ? null : log.event_id)}
                    className="w-full text-left flex items-start justify-between group-hover:bg-admin-surface2/30 -mx-2 px-2 py-1 rounded-lg transition-colors">
                    <div>
                      <p className="text-sm text-admin-text font-body capitalize font-medium">{log.event_type.replace(/_/g, ' ')}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] font-data text-admin-muted">{selectedApp?.application_number || 'Unknown application'}</span>
                        <span className="text-[10px] text-admin-muted">•</span>
                        <span className={`text-[10px] ${log.actor_id ? 'text-admin-gold' : 'text-admin-accent'}`}>
                          {log.actor_id ? `User ${log.actor_id}` : 'System'}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-admin-muted font-data">{new Date(log.timestamp).toLocaleString()}</span>
                      {isExpanded ? <ChevronDown size={12} className="text-admin-muted" /> : <ChevronRight size={12} className="text-admin-muted" />}
                    </div>
                  </button>

                  {isExpanded && hasDetails && (
                    <div className="mt-2 ml-0 p-3 bg-admin-bg border border-admin-border rounded-lg animate-fade-in">
                      <pre className="text-xs font-data text-admin-muted whitespace-pre-wrap">
                        {JSON.stringify(details, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default AuditLogPage;
