import React, { useState } from 'react';
import { Search, Filter, Download, Eye, Clock, User, FileText, X, CheckCircle, AlertTriangle, TrendingUp } from 'lucide-react';

interface AuditEvent {
  id: string;
  timestamp: string;
  event_type: string;
  user_id: string;
  actor_id: string;
  actor_name: string;
  application_id?: string;
  model_version?: string;
  decision?: string;
  decision_reason?: string;
  input_snapshot?: any;
  model_output?: any;
  policy_results?: any;
}

interface AuditLogViewerProps {
  events: AuditEvent[];
  loading?: boolean;
}

const AuditLogViewer: React.FC<AuditLogViewerProps> = ({ events, loading = false }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('all');
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);

  const filteredEvents = events.filter((event) => {
    const matchesSearch =
      event.event_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      event.actor_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (event.application_id && event.application_id.includes(searchTerm));
    const matchesType = eventTypeFilter === 'all' || event.event_type === eventTypeFilter;
    return matchesSearch && matchesType;
  });

  const eventTypes = Array.from(new Set(events.map((e) => e.event_type)));

  const getEventIcon = (eventType: string) => {
    if (eventType.includes('submit')) return <FileText size={16} className="text-barclays-blue" />;
    if (eventType.includes('decision')) return <CheckCircle size={16} className="text-risk-low" />;
    if (eventType.includes('override')) return <AlertTriangle size={16} className="text-risk-very_high" />;
    if (eventType.includes('simulate')) return <TrendingUp size={16} className="text-barclays-teal" />;
    return <Clock size={16} className="text-user-muted" />;
  };

  const getEventColor = (eventType: string) => {
    if (eventType.includes('submit')) return 'bg-blue-50 border-blue-200';
    if (eventType.includes('decision')) return 'bg-green-50 border-green-200';
    if (eventType.includes('override')) return 'bg-red-50 border-red-200';
    if (eventType.includes('simulate')) return 'bg-teal-50 border-teal-200';
    return 'bg-gray-50 border-gray-200';
  };

  const exportToCSV = () => {
    const headers = ['Timestamp', 'Event Type', 'Actor', 'Application ID', 'Decision', 'Model Version'];
    const rows = filteredEvents.map((e) => [
      e.timestamp,
      e.event_type,
      e.actor_name,
      e.application_id || '',
      e.decision || '',
      e.model_version || '',
    ]);
    const csv = [headers, ...rows].map((row) => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_log_${new Date().toISOString()}.csv`;
    a.click();
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-user-muted" />
          <input
            type="text"
            placeholder="Search by event type, actor, or application ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-user-border rounded-card text-sm focus:outline-none focus:border-barclays-navy"
          />
        </div>
        <div className="relative">
          <Filter size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-user-muted" />
          <select
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            className="pl-10 pr-8 py-2 border border-user-border rounded-card text-sm focus:outline-none focus:border-barclays-navy appearance-none bg-white"
          >
            <option value="all">All Events</option>
            {eventTypes.map((type) => (
              <option key={type} value={type}>
                {type.replace(/_/g, ' ')}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={exportToCSV}
          className="px-4 py-2 bg-barclays-navy text-white rounded-card text-sm font-medium hover:bg-barclays-blue transition-colors flex items-center gap-2"
        >
          <Download size={16} />
          Export CSV
        </button>
      </div>

      {/* Timeline */}
      <div className="bg-white border border-user-border rounded-card">
        {loading ? (
          <div className="p-8 text-center text-user-muted">Loading audit events...</div>
        ) : filteredEvents.length === 0 ? (
          <div className="p-8 text-center text-user-muted">No audit events found</div>
        ) : (
          <div className="divide-y divide-user-border max-h-[600px] overflow-y-auto">
            {filteredEvents.map((event) => (
              <div
                key={event.id}
                className="p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                onClick={() => setSelectedEvent(event)}
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg border ${getEventColor(event.event_type)}`}>
                    {getEventIcon(event.event_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <p className="text-sm font-medium text-user-text">
                        {event.event_type.replace(/_/g, ' ').toUpperCase()}
                      </p>
                      <span className="text-xs text-user-muted whitespace-nowrap">
                        {new Date(event.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-user-muted">
                      <span className="flex items-center gap-1">
                        <User size={12} />
                        {event.actor_name}
                      </span>
                      {event.application_id && (
                        <span className="flex items-center gap-1">
                          <FileText size={12} />
                          {event.application_id.slice(0, 8)}...
                        </span>
                      )}
                      {event.decision && (
                        <span className={`px-2 py-0.5 rounded-pill font-medium ${
                          event.decision === 'approved' ? 'bg-green-100 text-risk-low' :
                          event.decision === 'rejected' ? 'bg-red-100 text-risk-very_high' :
                          'bg-yellow-100 text-risk-medium'
                        }`}>
                          {event.decision.toUpperCase()}
                        </span>
                      )}
                    </div>
                  </div>
                  <button className="p-1 hover:bg-gray-100 rounded transition-colors">
                    <Eye size={16} className="text-user-muted" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Event Detail Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setSelectedEvent(null)} />
          <div className="relative bg-white rounded-card shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="sticky top-0 bg-barclays-navy text-white px-6 py-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Audit Event Details</h3>
              <button onClick={() => setSelectedEvent(null)} className="p-1 hover:bg-white/10 rounded">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-user-muted mb-1">Event Type</p>
                  <p className="font-medium text-user-text">{selectedEvent.event_type}</p>
                </div>
                <div>
                  <p className="text-user-muted mb-1">Timestamp</p>
                  <p className="font-medium text-user-text font-data">
                    {new Date(selectedEvent.timestamp).toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-user-muted mb-1">Actor</p>
                  <p className="font-medium text-user-text">{selectedEvent.actor_name}</p>
                </div>
                {selectedEvent.application_id && (
                  <div>
                    <p className="text-user-muted mb-1">Application ID</p>
                    <p className="font-medium text-user-text font-data">{selectedEvent.application_id}</p>
                  </div>
                )}
                {selectedEvent.model_version && (
                  <div>
                    <p className="text-user-muted mb-1">Model Version</p>
                    <p className="font-medium text-user-text font-data">{selectedEvent.model_version}</p>
                  </div>
                )}
                {selectedEvent.decision && (
                  <div>
                    <p className="text-user-muted mb-1">Decision</p>
                    <p className="font-medium text-user-text">{selectedEvent.decision.toUpperCase()}</p>
                  </div>
                )}
              </div>
              {selectedEvent.model_output && (
                <div>
                  <p className="text-sm font-medium text-user-text mb-2">Model Output</p>
                  <pre className="bg-gray-50 border border-user-border rounded-card p-3 text-xs overflow-x-auto">
                    {JSON.stringify(selectedEvent.model_output, null, 2)}
                  </pre>
                </div>
              )}
              {selectedEvent.policy_results && (
                <div>
                  <p className="text-sm font-medium text-user-text mb-2">Policy Results</p>
                  <pre className="bg-gray-50 border border-user-border rounded-card p-3 text-xs overflow-x-auto">
                    {JSON.stringify(selectedEvent.policy_results, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="text-sm text-user-muted">
        Showing {filteredEvents.length} of {events.length} events
      </div>
    </div>
  );
};

export default AuditLogViewer;
