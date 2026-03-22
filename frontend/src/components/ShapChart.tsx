import React from 'react';

interface ShapFactor {
  feature: string;
  value: number;
  displayName?: string;
}

interface ShapChartProps {
  positiveFactors: ShapFactor[];
  negativeFactors: ShapFactor[];
  compact?: boolean;
}

const featureDisplayNames: Record<string, string> = {
  income_stability: 'Income Stability',
  low_delinquency: 'Low Delinquency History',
  land_collateral_value: 'Land Collateral Value',
  platform_tenure: 'Platform Tenure',
  consistent_earnings: 'Consistent Earnings',
  debt_burden: 'Debt Burden',
  recent_late_payment: 'Recent Late Payment',
  no_prior_credit_history: 'No Prior Credit History',
  seasonal_income_flag: 'Seasonal Income Pattern',
  income_variability: 'Income Variability',
  revolving_utilization: 'Revolving Utilization',
  number_of_dependents: 'Number of Dependents',
};

const cleanFeatureName = (name: string): string => {
  return featureDisplayNames[name] || name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
};

const ShapChart: React.FC<ShapChartProps> = ({ positiveFactors, negativeFactors, compact = false }) => {
  const allFactors = [
    ...positiveFactors.map((f) => ({ ...f, direction: 'positive' as const })),
    ...negativeFactors.map((f) => ({ ...f, value: -Math.abs(f.value), direction: 'negative' as const })),
  ].sort((a, b) => Math.abs(b.value) - Math.abs(a.value));

  const maxAbsValue = Math.max(...allFactors.map((f) => Math.abs(f.value)), 0.01);
  const barHeight = compact ? 28 : 36;

  return (
    <div className="w-full space-y-1">
      {allFactors.slice(0, compact ? 5 : 10).map((factor, index) => {
        const barWidth = (Math.abs(factor.value) / maxAbsValue) * 100;
        const isPositive = factor.direction === 'positive';
        return (
          <div
            key={factor.feature}
            className="flex items-center gap-3 group"
            style={{ height: `${barHeight}px`, animationDelay: `${index * 60}ms` }}
          >
            <span
              className="text-xs text-right shrink-0 text-user-muted font-body"
              style={{ width: compact ? '120px' : '160px' }}
            >
              {cleanFeatureName(factor.feature)}
            </span>
            <div className="flex-1 flex items-center" style={{ height: '16px' }}>
              <div className="relative w-full h-full bg-gray-100 rounded-full overflow-hidden">
                {isPositive ? (
                  <div
                    className="absolute left-1/2 h-full rounded-r-full transition-all duration-500 ease-smooth"
                    style={{
                      width: `${barWidth / 2}%`,
                      background: 'linear-gradient(90deg, #10B981, #059669)',
                    }}
                  />
                ) : (
                  <div
                    className="absolute right-1/2 h-full rounded-l-full transition-all duration-500 ease-smooth"
                    style={{
                      width: `${barWidth / 2}%`,
                      background: 'linear-gradient(270deg, #EF4444, #DC2626)',
                    }}
                  />
                )}
                <div className="absolute left-1/2 top-0 w-px h-full bg-gray-300" />
              </div>
            </div>
            <span className={`text-xs font-data shrink-0 w-12 text-right ${isPositive ? 'text-risk-low' : 'text-risk-very_high'}`}>
              {isPositive ? '+' : ''}{factor.value.toFixed(3)}
            </span>
          </div>
        );
      })}
      <div className="flex items-center gap-3 mt-3 text-xs text-user-muted">
        <span style={{ width: '160px' }} />
        <div className="flex-1 flex justify-between px-2">
          <span className="text-risk-very_high">← Hurting score</span>
          <span className="text-risk-low">Helping score →</span>
        </div>
        <span className="w-12" />
      </div>
    </div>
  );
};

export default ShapChart;
