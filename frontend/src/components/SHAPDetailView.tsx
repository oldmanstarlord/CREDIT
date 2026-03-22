import React, { useState } from 'react';
import { TrendingUp, TrendingDown, Info, ChevronDown, ChevronUp } from 'lucide-react';

interface ShapFeature {
  feature: string;
  value: any;
  shap_value: number;
  base_value: number;
  feature_display_name?: string;
}

interface SHAPDetailViewProps {
  shapData: {
    base_value: number;
    features: ShapFeature[];
    final_prediction: number;
    top_positive_factors: Array<{ feature: string; value: number }>;
    top_negative_factors: Array<{ feature: string; value: number }>;
  };
  creditScore: number;
}

const featureDescriptions: Record<string, string> = {
  income_stability: 'Measures consistency of income over time',
  repayment_capacity: 'Ability to repay based on income and expenses',
  debt_burden: 'Existing debt obligations relative to income',
  credit_history_length: 'Duration of credit history',
  recent_late_payment: 'Recent payment delays or defaults',
  revolving_utilization: 'Credit card utilization ratio',
  number_of_dependents: 'Financial dependents count',
  land_collateral_value: 'Value of land offered as collateral',
  platform_tenure: 'Duration on gig/platform',
  consistent_earnings: 'Earnings consistency pattern',
};

const SHAPDetailView: React.FC<SHAPDetailViewProps> = ({ shapData, creditScore }) => {
  const [expandedFeature, setExpandedFeature] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'impact' | 'alphabetical'>('impact');

  const sortedFeatures = [...shapData.features].sort((a, b) => {
    if (sortBy === 'impact') {
      return Math.abs(b.shap_value) - Math.abs(a.shap_value);
    }
    return a.feature.localeCompare(b.feature);
  });

  const maxAbsShap = Math.max(...shapData.features.map((f) => Math.abs(f.shap_value)));

  const formatFeatureName = (name: string) => {
    return name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  };

  const formatFeatureValue = (value: any) => {
    if (typeof value === 'number') {
      return value.toFixed(2);
    }
    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No';
    }
    return String(value);
  };

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <div className="bg-gradient-to-br from-barclays-navy to-barclays-teal text-white rounded-card p-6">
        <h3 className="text-lg font-semibold mb-4 font-heading">
          SHAP Explanation Summary
        </h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm opacity-80 mb-1">Base Value</p>
            <p className="text-2xl font-bold font-data">
              {shapData.base_value.toFixed(3)}
            </p>
            <p className="text-xs opacity-70 mt-1">Average prediction</p>
          </div>
          <div>
            <p className="text-sm opacity-80 mb-1">Final Prediction</p>
            <p className="text-2xl font-bold font-data">
              {shapData.final_prediction.toFixed(3)}
            </p>
            <p className="text-xs opacity-70 mt-1">Model output</p>
          </div>
          <div>
            <p className="text-sm opacity-80 mb-1">Credit Score</p>
            <p className="text-2xl font-bold font-data">
              {creditScore}
            </p>
            <p className="text-xs opacity-70 mt-1">Scaled score</p>
          </div>
        </div>
      </div>

      {/* Top Factors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Positive Factors */}
        <div className="bg-green-50 border border-green-200 rounded-card p-4">
          <h4 className="text-sm font-semibold text-risk-low mb-3 flex items-center gap-2">
            <TrendingUp size={16} />
            Top Positive Factors
          </h4>
          <div className="space-y-2">
            {shapData.top_positive_factors.slice(0, 5).map((factor, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm text-user-text">
                  {formatFeatureName(factor.feature)}
                </span>
                <span className="text-sm font-bold text-risk-low font-data">
                  +{factor.value.toFixed(3)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Negative Factors */}
        <div className="bg-red-50 border border-red-200 rounded-card p-4">
          <h4 className="text-sm font-semibold text-risk-very_high mb-3 flex items-center gap-2">
            <TrendingDown size={16} />
            Top Negative Factors
          </h4>
          <div className="space-y-2">
            {shapData.top_negative_factors.slice(0, 5).map((factor, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm text-user-text">
                  {formatFeatureName(factor.feature)}
                </span>
                <span className="text-sm font-bold text-risk-very_high font-data">
                  {factor.value.toFixed(3)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Sort Controls */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-user-text">
          All Features ({shapData.features.length})
        </h3>
        <div className="flex gap-2">
          <button
            onClick={() => setSortBy('impact')}
            className={`px-3 py-1.5 text-xs font-medium rounded-pill transition-colors ${
              sortBy === 'impact'
                ? 'bg-barclays-navy text-white'
                : 'bg-gray-100 text-user-text hover:bg-gray-200'
            }`}
          >
            Sort by Impact
          </button>
          <button
            onClick={() => setSortBy('alphabetical')}
            className={`px-3 py-1.5 text-xs font-medium rounded-pill transition-colors ${
              sortBy === 'alphabetical'
                ? 'bg-barclays-navy text-white'
                : 'bg-gray-100 text-user-text hover:bg-gray-200'
            }`}
          >
            Sort A-Z
          </button>
        </div>
      </div>

      {/* Feature List */}
      <div className="space-y-2">
        {sortedFeatures.map((feature) => {
          const isExpanded = expandedFeature === feature.feature;
          const isPositive = feature.shap_value > 0;
          const barWidth = (Math.abs(feature.shap_value) / maxAbsShap) * 100;

          return (
            <div
              key={feature.feature}
              className="bg-white border border-user-border rounded-card overflow-hidden"
            >
              <button
                onClick={() => setExpandedFeature(isExpanded ? null : feature.feature)}
                className="w-full p-4 text-left hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-user-text">
                      {formatFeatureName(feature.feature)}
                    </span>
                    {featureDescriptions[feature.feature] && (
                      <Info size={14} className="text-user-muted" />
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-sm font-bold font-data ${isPositive ? 'text-risk-low' : 'text-risk-very_high'}`}>
                      {isPositive ? '+' : ''}{feature.shap_value.toFixed(3)}
                    </span>
                    {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </div>
                </div>

                {/* Impact Bar */}
                <div className="relative h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`absolute h-full transition-all duration-300 ${
                      isPositive ? 'bg-risk-low left-1/2' : 'bg-risk-very_high right-1/2'
                    }`}
                    style={{ width: `${barWidth / 2}%` }}
                  />
                  <div className="absolute left-1/2 top-0 w-px h-full bg-gray-300" />
                </div>
              </button>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-user-border bg-gray-50">
                  <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
                    <div>
                      <p className="text-user-muted mb-1">Feature Value</p>
                      <p className="font-medium text-user-text font-data">
                        {formatFeatureValue(feature.value)}
                      </p>
                    </div>
                    <div>
                      <p className="text-user-muted mb-1">SHAP Value</p>
                      <p className={`font-medium font-data ${isPositive ? 'text-risk-low' : 'text-risk-very_high'}`}>
                        {feature.shap_value.toFixed(4)}
                      </p>
                    </div>
                  </div>
                  {featureDescriptions[feature.feature] && (
                    <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-card">
                      <p className="text-xs text-user-text">
                        <strong>What this means:</strong> {featureDescriptions[feature.feature]}
                      </p>
                    </div>
                  )}
                  <div className="mt-3 text-xs text-user-muted">
                    <p>
                      This feature {isPositive ? 'increased' : 'decreased'} the credit score by approximately{' '}
                      <strong>{Math.abs(feature.shap_value * 100).toFixed(1)} points</strong> from the base prediction.
                    </p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Explanation Footer */}
      <div className="bg-blue-50 border border-blue-200 rounded-card p-4">
        <h4 className="text-sm font-semibold text-barclays-navy mb-2">
          How to Read SHAP Values
        </h4>
        <ul className="text-xs text-user-text space-y-1">
          <li>• <strong>Positive values (green)</strong> increase the credit score</li>
          <li>• <strong>Negative values (red)</strong> decrease the credit score</li>
          <li>• <strong>Base value</strong> is the average prediction across all applications</li>
          <li>• <strong>Final prediction</strong> = Base value + Sum of all SHAP values</li>
          <li>• Larger absolute values indicate stronger impact on the decision</li>
        </ul>
      </div>
    </div>
  );
};

export default SHAPDetailView;
