import React from 'react';
import { TrendingDown, AlertCircle, DollarSign, Percent } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface PortfolioRiskData {
  totalExposure: number;
  expectedLoss: number;
  valueAtRisk95: number;
  valueAtRisk99: number;
  concentrationRisk: number;
  lossDistribution: Array<{ loss: number; probability: number }>;
  exposureByRisk: Array<{ risk_band: string; exposure: number; count: number }>;
  vintageAnalysis: Array<{ month: string; default_rate: number; exposure: number }>;
  stressTestResults: Array<{ scenario: string; loss: number; impact: number }>;
}

interface PortfolioRiskViewProps {
  data: PortfolioRiskData;
}

const PortfolioRiskView: React.FC<PortfolioRiskViewProps> = ({ data }) => {
  const formatCurrency = (value: number) => {
    if (value >= 10000000) return `₹${(value / 10000000).toFixed(1)}Cr`;
    if (value >= 100000) return `₹${(value / 100000).toFixed(1)}L`;
    return `₹${value.toLocaleString()}`;
  };

  const riskMetrics = [
    {
      label: 'Total Exposure',
      value: formatCurrency(data.totalExposure),
      icon: DollarSign,
      color: 'text-barclays-blue',
      bgColor: 'bg-blue-50',
    },
    {
      label: 'Expected Loss',
      value: formatCurrency(data.expectedLoss),
      subtext: `${((data.expectedLoss / data.totalExposure) * 100).toFixed(2)}% of exposure`,
      icon: TrendingDown,
      color: 'text-risk-medium',
      bgColor: 'bg-yellow-50',
    },
    {
      label: 'VaR (95%)',
      value: formatCurrency(data.valueAtRisk95),
      subtext: '95% confidence',
      icon: AlertCircle,
      color: 'text-risk-high',
      bgColor: 'bg-orange-50',
    },
    {
      label: 'VaR (99%)',
      value: formatCurrency(data.valueAtRisk99),
      subtext: '99% confidence',
      icon: AlertCircle,
      color: 'text-risk-very_high',
      bgColor: 'bg-red-50',
    },
    {
      label: 'Concentration Risk',
      value: `${data.concentrationRisk.toFixed(1)}%`,
      subtext: 'Top 10 borrowers',
      icon: Percent,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Risk Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {riskMetrics.map((metric, index) => {
          const Icon = metric.icon;
          return (
            <div
              key={index}
              className="bg-white border border-user-border rounded-card p-4"
            >
              <div className={`p-2 rounded-lg ${metric.bgColor} w-fit mb-3`}>
                <Icon size={20} className={metric.color} />
              </div>
              <p className="text-2xl font-bold text-user-text font-data mb-1">
                {metric.value}
              </p>
              <p className="text-xs text-user-muted">{metric.label}</p>
              {metric.subtext && (
                <p className="text-xs text-user-muted mt-1">{metric.subtext}</p>
              )}
            </div>
          );
        })}
      </div>

      {/* Loss Distribution (Monte Carlo) */}
      <div className="bg-white border border-user-border rounded-card p-4">
        <h3 className="text-sm font-semibold text-user-text mb-4">
          Loss Distribution (Monte Carlo Simulation - 10,000 iterations)
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data.lossDistribution}>
            <defs>
              <linearGradient id="lossGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#EF4444" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#EF4444" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
            <XAxis
              dataKey="loss"
              tick={{ fontSize: 12 }}
              label={{ value: 'Loss Amount (₹)', position: 'insideBottom', offset: -5 }}
              tickFormatter={(value) => formatCurrency(value)}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              label={{ value: 'Probability', angle: -90, position: 'insideLeft' }}
              tickFormatter={(value) => `${(value * 100).toFixed(1)}%`}
            />
            <Tooltip
              formatter={(value: any) => [`${(value * 100).toFixed(2)}%`, 'Probability']}
              labelFormatter={(label) => `Loss: ${formatCurrency(label)}`}
            />
            <Area
              type="monotone"
              dataKey="probability"
              stroke="#EF4444"
              strokeWidth={2}
              fill="url(#lossGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
        <div className="mt-4 grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-xs text-user-muted mb-1">Expected Loss</p>
            <p className="text-lg font-bold text-user-text font-data">
              {formatCurrency(data.expectedLoss)}
            </p>
          </div>
          <div>
            <p className="text-xs text-user-muted mb-1">VaR 95%</p>
            <p className="text-lg font-bold text-risk-high font-data">
              {formatCurrency(data.valueAtRisk95)}
            </p>
          </div>
          <div>
            <p className="text-xs text-user-muted mb-1">VaR 99%</p>
            <p className="text-lg font-bold text-risk-very_high font-data">
              {formatCurrency(data.valueAtRisk99)}
            </p>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Exposure by Risk Band */}
        <div className="bg-white border border-user-border rounded-card p-4">
          <h3 className="text-sm font-semibold text-user-text mb-4">
            Exposure by Risk Band
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data.exposureByRisk}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="risk_band" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(value) => formatCurrency(value)} />
              <Tooltip formatter={(value: any) => [formatCurrency(value), 'Exposure']} />
              <Legend />
              <Bar dataKey="exposure" fill="#00AEEF" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Vintage Analysis */}
        <div className="bg-white border border-user-border rounded-card p-4">
          <h3 className="text-sm font-semibold text-user-text mb-4">
            Vintage Analysis - Default Rate Trend
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={data.vintageAnalysis}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="month" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(value) => `${value}%`} />
              <Tooltip formatter={(value: any) => [`${value}%`, 'Default Rate']} />
              <Legend />
              <Line
                type="monotone"
                dataKey="default_rate"
                stroke="#EF4444"
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Stress Test Results */}
      <div className="bg-white border border-user-border rounded-card p-4">
        <h3 className="text-sm font-semibold text-user-text mb-4">
          Stress Test Scenarios
        </h3>
        <div className="space-y-3">
          {data.stressTestResults.map((scenario, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-card"
            >
              <div className="flex-1">
                <p className="text-sm font-medium text-user-text mb-1">
                  {scenario.scenario}
                </p>
                <div className="flex items-center gap-4 text-xs text-user-muted">
                  <span>Projected Loss: {formatCurrency(scenario.loss)}</span>
                  <span>•</span>
                  <span>Impact: {scenario.impact.toFixed(1)}% of portfolio</span>
                </div>
              </div>
              <div className="text-right">
                <p className={`text-lg font-bold font-data ${scenario.impact > 10 ? 'text-risk-very_high' : scenario.impact > 5 ? 'text-risk-medium' : 'text-risk-low'}`}>
                  {scenario.impact.toFixed(1)}%
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Risk Alerts */}
      <div className="bg-red-50 border border-red-200 rounded-card p-4">
        <div className="flex gap-3">
          <AlertCircle size={20} className="text-risk-very_high shrink-0 mt-0.5" />
          <div className="text-sm text-red-800">
            <p className="font-semibold mb-2">Portfolio Risk Alerts</p>
            <ul className="list-disc list-inside space-y-1 text-xs">
              {data.concentrationRisk > 20 && (
                <li>High concentration risk detected: Top 10 borrowers represent {data.concentrationRisk.toFixed(1)}% of portfolio</li>
              )}
              {(data.expectedLoss / data.totalExposure) * 100 > 5 && (
                <li>Expected loss ratio exceeds 5% threshold</li>
              )}
              {data.vintageAnalysis[data.vintageAnalysis.length - 1]?.default_rate > 3 && (
                <li>Recent vintage showing elevated default rates</li>
              )}
              {data.stressTestResults.some(s => s.impact > 15) && (
                <li>Severe stress scenario shows potential loss &gt; 15% of portfolio</li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioRiskView;
