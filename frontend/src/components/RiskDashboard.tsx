import React from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, Users, DollarSign, CheckCircle } from 'lucide-react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface RiskDashboardProps {
  data: {
    totalApplications: number;
    approvalRate: number;
    avgCreditScore: number;
    totalDisbursed: number;
    portfolioAtRisk: number;
    defaultRate: number;
    applicationsByRisk: Array<{ name: string; value: number }>;
    applicationsTrend: Array<{ date: string; approved: number; rejected: number; hold: number }>;
    scoreDistribution: Array<{ range: string; count: number }>;
    categoryBreakdown: Array<{ category: string; count: number; avgScore: number }>;
  };
}

const COLORS = {
  low: '#10B981',
  medium: '#F59E0B',
  high: '#F97316',
  very_high: '#EF4444',
};

const RiskDashboard: React.FC<RiskDashboardProps> = ({ data }) => {
  const kpis = [
    {
      label: 'Total Applications',
      value: data.totalApplications.toLocaleString(),
      icon: Users,
      color: 'text-barclays-blue',
      bgColor: 'bg-blue-50',
      trend: '+12%',
      trendUp: true,
    },
    {
      label: 'Approval Rate',
      value: `${data.approvalRate.toFixed(1)}%`,
      icon: CheckCircle,
      color: 'text-risk-low',
      bgColor: 'bg-green-50',
      trend: '+3.2%',
      trendUp: true,
    },
    {
      label: 'Avg Credit Score',
      value: Math.round(data.avgCreditScore),
      icon: TrendingUp,
      color: 'text-barclays-teal',
      bgColor: 'bg-teal-50',
      trend: '+8 pts',
      trendUp: true,
    },
    {
      label: 'Total Disbursed',
      value: `₹${(data.totalDisbursed / 10000000).toFixed(1)}Cr`,
      icon: DollarSign,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      trend: '+18%',
      trendUp: true,
    },
    {
      label: 'Portfolio at Risk',
      value: `${data.portfolioAtRisk.toFixed(1)}%`,
      icon: AlertTriangle,
      color: 'text-risk-medium',
      bgColor: 'bg-yellow-50',
      trend: '-1.2%',
      trendUp: false,
    },
    {
      label: 'Default Rate',
      value: `${data.defaultRate.toFixed(2)}%`,
      icon: TrendingDown,
      color: 'text-risk-very_high',
      bgColor: 'bg-red-50',
      trend: '-0.5%',
      trendUp: false,
    },
  ];

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {kpis.map((kpi, index) => {
          const Icon = kpi.icon;
          return (
            <div
              key={index}
              className="bg-white border border-user-border rounded-card p-4 hover:shadow-card-user transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`p-2 rounded-lg ${kpi.bgColor}`}>
                  <Icon size={20} className={kpi.color} />
                </div>
                <div className={`flex items-center gap-1 text-xs font-medium ${kpi.trendUp ? 'text-risk-low' : 'text-risk-very_high'}`}>
                  {kpi.trendUp ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                  {kpi.trend}
                </div>
              </div>
              <p className="text-2xl font-bold text-user-text font-data mb-1">
                {kpi.value}
              </p>
              <p className="text-xs text-user-muted">{kpi.label}</p>
            </div>
          );
        })}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Applications by Risk */}
        <div className="bg-white border border-user-border rounded-card p-4">
          <h3 className="text-sm font-semibold text-user-text mb-4">
            Applications by Risk Band
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={data.applicationsByRisk}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {data.applicationsByRisk.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[entry.name.toLowerCase() as keyof typeof COLORS]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Score Distribution */}
        <div className="bg-white border border-user-border rounded-card p-4">
          <h3 className="text-sm font-semibold text-user-text mb-4">
            Credit Score Distribution
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data.scoreDistribution}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="range" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#00AEEF" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 gap-6">
        {/* Applications Trend */}
        <div className="bg-white border border-user-border rounded-card p-4">
          <h3 className="text-sm font-semibold text-user-text mb-4">
            Application Decisions Trend (Last 30 Days)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data.applicationsTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="approved" stroke="#10B981" strokeWidth={2} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="rejected" stroke="#EF4444" strokeWidth={2} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="hold" stroke="#F59E0B" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Category Breakdown */}
        <div className="bg-white border border-user-border rounded-card p-4">
          <h3 className="text-sm font-semibold text-user-text mb-4">
            Performance by User Category
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.categoryBreakdown} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis dataKey="category" type="category" tick={{ fontSize: 12 }} width={120} />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#00AEEF" name="Applications" radius={[0, 4, 4, 0]} />
              <Bar dataKey="avgScore" fill="#10B981" name="Avg Score" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default RiskDashboard;
