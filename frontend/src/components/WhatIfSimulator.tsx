import React, { useState } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface WhatIfSimulatorProps {
  applicationId: string;
  currentScore: number;
  currentPD: number;
  currentIncome: number;
  currentAmount: number;
  currentTenure: number;
  onSimulate: (params: SimulationParams) => Promise<SimulationResult>;
}

interface SimulationParams {
  adjusted_income_percentage?: number;
  adjusted_loan_amount?: number;
  adjusted_tenure_months?: number;
}

interface SimulationResult {
  adjusted_credit_score: number;
  adjusted_probability_of_default: number;
  adjusted_eligibility: string;
  score_change: number;
  pd_change: number;
}

const WhatIfSimulator: React.FC<WhatIfSimulatorProps> = ({
  applicationId,
  currentScore,
  currentPD,
  currentIncome,
  currentAmount,
  currentTenure,
  onSimulate,
}) => {
  const [incomeAdjustment, setIncomeAdjustment] = useState(0);
  const [loanAmount, setLoanAmount] = useState(currentAmount);
  const [tenure, setTenure] = useState(currentTenure);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const params: SimulationParams = {
        adjusted_income_percentage: incomeAdjustment,
        adjusted_loan_amount: loanAmount,
        adjusted_tenure_months: tenure,
      };
      const simulationResult = await onSimulate(params);
      setResult(simulationResult);
    } catch (error) {
      console.error('Simulation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getChangeIcon = (change: number) => {
    if (change > 0) return <TrendingUp className="w-5 h-5 text-green-500" />;
    if (change < 0) return <TrendingDown className="w-5 h-5 text-red-500" />;
    return <Minus className="w-5 h-5 text-gray-500" />;
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-6">What-If Simulator</h3>
      <p className="text-sm text-gray-600 mb-6">
        Adjust the parameters below to see how changes would affect your credit score and eligibility.
      </p>

      {/* Input Controls */}
      <div className="space-y-6 mb-6">
        {/* Income Adjustment */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Income Adjustment
          </label>
          <div className="flex items-center space-x-4">
            <input
              type="range"
              min="-50"
              max="50"
              value={incomeAdjustment}
              onChange={(e) => setIncomeAdjustment(parseInt(e.target.value))}
              className="flex-1"
            />
            <span className="text-lg font-semibold text-gray-900 w-20 text-right">
              {incomeAdjustment > 0 ? '+' : ''}{incomeAdjustment}%
            </span>
          </div>
          <div className="text-sm text-gray-600 mt-1">
            Adjusted Income: {formatCurrency(currentIncome * (1 + incomeAdjustment / 100))}
          </div>
        </div>

        {/* Loan Amount */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Loan Amount
          </label>
          <input
            type="number"
            value={loanAmount}
            onChange={(e) => setLoanAmount(parseInt(e.target.value) || 0)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            min="10000"
            step="10000"
          />
          <div className="text-sm text-gray-600 mt-1">
            Current: {formatCurrency(currentAmount)}
          </div>
        </div>

        {/* Tenure */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Loan Tenure (months)
          </label>
          <input
            type="number"
            value={tenure}
            onChange={(e) => setTenure(parseInt(e.target.value) || 12)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            min="6"
            max="60"
          />
          <div className="text-sm text-gray-600 mt-1">
            Current: {currentTenure} months
          </div>
        </div>
      </div>

      {/* Simulate Button */}
      <button
        onClick={handleSimulate}
        disabled={loading}
        className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? 'Simulating...' : 'Run Simulation'}
      </button>

      {/* Results */}
      {result && (
        <div className="mt-6 p-6 bg-gray-50 rounded-lg space-y-4">
          <h4 className="font-semibold text-gray-900 mb-4">Simulation Results</h4>

          {/* Credit Score Change */}
          <div className="flex justify-between items-center p-4 bg-white rounded-lg">
            <div>
              <div className="text-sm text-gray-600">Credit Score</div>
              <div className="text-2xl font-bold text-gray-900">
                {result.adjusted_credit_score}
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {getChangeIcon(result.score_change)}
              <span className={`text-lg font-semibold ${getChangeColor(result.score_change)}`}>
                {result.score_change > 0 ? '+' : ''}{result.score_change}
              </span>
            </div>
          </div>

          {/* PD Change */}
          <div className="flex justify-between items-center p-4 bg-white rounded-lg">
            <div>
              <div className="text-sm text-gray-600">Default Probability</div>
              <div className="text-2xl font-bold text-gray-900">
                {(result.adjusted_probability_of_default * 100).toFixed(2)}%
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {getChangeIcon(-result.pd_change)}
              <span className={`text-lg font-semibold ${getChangeColor(-result.pd_change)}`}>
                {result.pd_change > 0 ? '+' : ''}{(result.pd_change * 100).toFixed(2)}pp
              </span>
            </div>
          </div>

          {/* Eligibility */}
          <div className="p-4 bg-white rounded-lg">
            <div className="text-sm text-gray-600 mb-1">Eligibility Status</div>
            <div className={`text-xl font-bold ${
              result.adjusted_eligibility === 'APPROVED' ? 'text-green-600' :
              result.adjusted_eligibility === 'REJECTED' ? 'text-red-600' :
              'text-yellow-600'
            }`}>
              {result.adjusted_eligibility}
            </div>
          </div>

          {/* Disclaimer */}
          <div className="text-xs text-gray-500 mt-4">
            * This is a simulation only. Actual loan approval depends on full verification and review.
          </div>
        </div>
      )}
    </div>
  );
};

export default WhatIfSimulator;
