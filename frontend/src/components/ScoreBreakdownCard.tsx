import React from 'react';

interface PillarScore {
  name: string;
  score: number;
  maxScore: number;
  weight: number;
  description: string;
}

interface ScoreBreakdownCardProps {
  incomeStability: number;
  repaymentCapacity: number;
  spendingData: number;
  profileCompleteness: number;
  alternativeData: number;
}

const ScoreBreakdownCard: React.FC<ScoreBreakdownCardProps> = ({
  incomeStability,
  repaymentCapacity,
  spendingData,
  profileCompleteness,
  alternativeData,
}) => {
  const pillars: PillarScore[] = [
    {
      name: 'Income Stability',
      score: incomeStability,
      maxScore: 25,
      weight: 25,
      description: 'Consistency and predictability of your income',
    },
    {
      name: 'Repayment Capacity',
      score: repaymentCapacity,
      maxScore: 30,
      weight: 30,
      description: 'Your ability to afford monthly payments',
    },
    {
      name: 'Spending Patterns',
      score: spendingData,
      maxScore: 15,
      weight: 15,
      description: 'How you manage your expenses',
    },
    {
      name: 'Profile Completeness',
      score: profileCompleteness,
      maxScore: 10,
      weight: 10,
      description: 'Verification and documentation provided',
    },
    {
      name: 'Alternative Data',
      score: alternativeData,
      maxScore: 20,
      weight: 20,
      description: 'Bill payments, UPI, platform activity',
    },
  ];

  const getColorClass = (percentage: number) => {
    if (percentage >= 80) return 'bg-green-500';
    if (percentage >= 60) return 'bg-blue-500';
    if (percentage >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-6">Score Breakdown</h3>
      
      <div className="space-y-6">
        {pillars.map((pillar) => {
          const percentage = (pillar.score / pillar.maxScore) * 100;
          const colorClass = getColorClass(percentage);

          return (
            <div key={pillar.name} className="space-y-2">
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="font-semibold text-gray-900">{pillar.name}</h4>
                  <p className="text-sm text-gray-600">{pillar.description}</p>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-bold text-gray-900">
                    {pillar.score}
                  </span>
                  <span className="text-sm text-gray-600">/{pillar.maxScore}</span>
                  <div className="text-xs text-gray-500">({pillar.weight}% weight)</div>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-full ${colorClass} transition-all duration-500 ease-out`}
                  style={{ width: `${percentage}%` }}
                />
              </div>

              {/* Percentage label */}
              <div className="text-right text-sm text-gray-600">
                {percentage.toFixed(0)}% of maximum
              </div>
            </div>
          );
        })}
      </div>

      {/* Total score */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <div className="flex justify-between items-center">
          <span className="text-lg font-semibold text-gray-900">Total Pillar Score</span>
          <span className="text-3xl font-bold text-blue-600">
            {incomeStability + repaymentCapacity + spendingData + profileCompleteness + alternativeData}
            <span className="text-lg text-gray-600">/100</span>
          </span>
        </div>
      </div>
    </div>
  );
};

export default ScoreBreakdownCard;
