import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Search, Filter, ArrowUpDown } from 'lucide-react';

interface Application {
  id: string;
  application_number: string;
  user_name: string;
  user_category: string;
  requested_amount: number;
  credit_score?: number;
  risk_band?: string;
  status: string;
  final_decision?: string;
  created_at: string;
  fraud_score?: number;
}

interface ApplicationTableProps {
  applications: Application[];
  onRowClick: (application: Application) => void;
  loading?: boolean;
}

type SortField = 'created_at' | 'credit_score' | 'requested_amount' | 'fraud_score';
type SortDirection = 'asc' | 'desc';

const ApplicationTable: React.FC<ApplicationTableProps> = ({
  applications,
  onRowClick,
  loading = false,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const filteredAndSorted = applications
    .filter((app) => {
      const matchesSearch =
        app.application_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
        app.user_name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || app.status === statusFilter;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      const aVal = a[sortField] ?? 0;
      const bVal = b[sortField] ?? 0;
      const multiplier = sortDirection === 'asc' ? 1 : -1;
      return aVal > bVal ? multiplier : -multiplier;
    });

  const getStatusBadge = (status: string) => {
    const configs: Record<string, { bg: string; text: string }> = {
      approved: { bg: 'bg-green-100', text: 'text-risk-low' },
      rejected: { bg: 'bg-red-100', text: 'text-risk-very_high' },
      hold: { bg: 'bg-yellow-100', text: 'text-risk-medium' },
      pre_screening: { bg: 'bg-blue-100', text: 'text-barclays-blue' },
      ml_scored: { bg: 'bg-purple-100', text: 'text-purple-700' },
    };
    const config = configs[status] || { bg: 'bg-gray-100', text: 'text-gray-700' };
    return (
      <span className={`px-2 py-1 rounded-pill text-xs font-medium ${config.bg} ${config.text}`}>
        {status.replace(/_/g, ' ').toUpperCase()}
      </span>
    );
  };

  const getRiskBadge = (riskBand?: string) => {
    if (!riskBand) return <span className="text-xs text-user-muted">—</span>;
    const configs: Record<string, { bg: string; text: string }> = {
      low: { bg: 'bg-green-100', text: 'text-risk-low' },
      medium: { bg: 'bg-yellow-100', text: 'text-risk-medium' },
      high: { bg: 'bg-orange-100', text: 'text-risk-high' },
      very_high: { bg: 'bg-red-100', text: 'text-risk-very_high' },
    };
    const config = configs[riskBand] || { bg: 'bg-gray-100', text: 'text-gray-700' };
    return (
      <span className={`px-2 py-1 rounded-pill text-xs font-medium ${config.bg} ${config.text}`}>
        {riskBand.toUpperCase()}
      </span>
    );
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-user-muted" />
          <input
            type="text"
            placeholder="Search by application number or name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-user-border rounded-card text-sm focus:outline-none focus:border-barclays-navy"
          />
        </div>
        <div className="relative">
          <Filter size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-user-muted" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="pl-10 pr-8 py-2 border border-user-border rounded-card text-sm focus:outline-none focus:border-barclays-navy appearance-none bg-white"
          >
            <option value="all">All Status</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="hold">Hold</option>
            <option value="pre_screening">Pre-Screening</option>
            <option value="ml_scored">ML Scored</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-user-border rounded-card">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-user-border">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-user-text">
                Application #
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-user-text">
                Borrower
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-user-text">
                Category
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-semibold text-user-text cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('requested_amount')}
              >
                <div className="flex items-center gap-1">
                  Amount
                  <ArrowUpDown size={14} />
                </div>
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-semibold text-user-text cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('credit_score')}
              >
                <div className="flex items-center gap-1">
                  Score
                  <ArrowUpDown size={14} />
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-user-text">
                Risk
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-user-text">
                Status
              </th>
              <th
                className="px-4 py-3 text-left text-xs font-semibold text-user-text cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('created_at')}
              >
                <div className="flex items-center gap-1">
                  Date
                  <ArrowUpDown size={14} />
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-user-muted">
                  Loading applications...
                </td>
              </tr>
            ) : filteredAndSorted.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-user-muted">
                  No applications found
                </td>
              </tr>
            ) : (
              filteredAndSorted.map((app) => (
                <tr
                  key={app.id}
                  onClick={() => onRowClick(app)}
                  className="border-b border-user-border hover:bg-barclays-lightblue cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3 text-sm font-medium text-barclays-navy">
                    {app.application_number}
                  </td>
                  <td className="px-4 py-3 text-sm text-user-text">
                    {app.user_name}
                  </td>
                  <td className="px-4 py-3 text-sm text-user-muted">
                    {app.user_category.replace(/_/g, ' ')}
                  </td>
                  <td className="px-4 py-3 text-sm font-data text-user-text">
                    ₹{app.requested_amount.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-sm font-data text-user-text">
                    {app.credit_score || '—'}
                  </td>
                  <td className="px-4 py-3">
                    {getRiskBadge(app.risk_band)}
                  </td>
                  <td className="px-4 py-3">
                    {getStatusBadge(app.status)}
                  </td>
                  <td className="px-4 py-3 text-sm text-user-muted">
                    {new Date(app.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Results count */}
      <div className="text-sm text-user-muted">
        Showing {filteredAndSorted.length} of {applications.length} applications
      </div>
    </div>
  );
};

export default ApplicationTable;
