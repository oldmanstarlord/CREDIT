import React from 'react';
import { CheckCircle, AlertCircle, Clock } from 'lucide-react';

interface LoanTermsCardProps {
  eligibility: 'APPROVED' | 'REJECTED' | 'HOLD';
  approvedAmount?: number;
  requestedAmount: number;
  tenureMonths?: number;
  interestRateMin?: number;
  interestRateMax?: number;
  estimatedEmiMin?: number;
  estimatedEmiMax?: number;
  decisionReason?: string;
}

const LoanTermsCard: React.FC<LoanTermsCardProps> = ({
  eligibility,
  approvedAmount,
  requestedAmount,
  tenureMonths,
  interestRateMin,
  interestRateMax,
  estimatedEmiMin,
  estimatedEmiMax,
  decisionReason,
}) => {
  const getStatusConfig = () => {
    switch (eligibility) {
      case 'APPROVED':
        return {
          icon: <CheckCircle className="w-12 h-12 text-green-500" />,
          title: 'Congratulations! Loan Approved',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          textColor: 'text-green-800',
        };
      case 'REJECTED':
        return {
          icon: <AlertCircle className="w-12 h-12 text-red-500" />,
          title: 'Application Not Approved',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          textColor: 'text-red-800',
        };
      case 'HOLD':
        return {
          icon: <Clock className="w-12 h-12 text-yellow-500" />,
          title: 'Under Review',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          textColor: 'text-yellow-800',
        };
      default:
        return {
          icon: <Clock className="w-12 h-12 text-gray-500" />,
          title: 'Processing',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          textColor: 'text-gray-800',
        };
    }
  };

  const config = getStatusConfig();

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <div className={`rounded-lg shadow-lg border-2 ${config.borderColor} ${config.bgColor} p-6`}>
      {/* Status Header */}
      <div className="flex items-center space-x-4 mb-6">
        {config.icon}
        <div>
          <h2 className={`text-2xl font-bold ${config.textColor}`}>{config.title}</h2>
          {decisionReason && (
            <p className="text-sm text-gray-600 mt-1">{decisionReason}</p>
          )}
        </div>
      </div>

      {/* Loan Terms (if approved) */}
      {eligibility === 'APPROVED' && approvedAmount && (
        <div className="space-y-4 bg-white rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Loan Terms</h3>

          {/* Approved Amount */}
          <div className="flex justify-between items-center py-3 border-b border-gray-200">
            <span className="text-gray-700">Approved Amount</span>
            <span className="text-2xl font-bold text-green-600">
              {formatCurrency(approvedAmount)}
            </span>
          </div>

          {approvedAmount < requestedAmount && (
            <div className="text-sm text-gray-600 -mt-2 mb-2">
              (Requested: {formatCurrency(requestedAmount)})
            </div>
          )}

          {/* Tenure */}
          {tenureMonths && (
            <div className="flex justify-between items-center py-3 border-b border-gray-200">
              <span className="text-gray-700">Loan Tenure</span>
              <span className="text-xl font-semibold text-gray-900">
                {tenureMonths} months
              </span>
            </div>
          )}

          {/* Interest Rate */}
          {interestRateMin !== undefined && interestRateMax !== undefined && (
            <div className="flex justify-between items-center py-3 border-b border-gray-200">
              <span className="text-gray-700">Interest Rate (per annum)</span>
              <span className="text-xl font-semibold text-gray-900">
                {interestRateMin.toFixed(2)}% - {interestRateMax.toFixed(2)}%
              </span>
            </div>
          )}

          {/* EMI */}
          {estimatedEmiMin !== undefined && estimatedEmiMax !== undefined && (
            <div className="flex justify-between items-center py-3">
              <span className="text-gray-700">Estimated Monthly EMI</span>
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">
                  {formatCurrency(estimatedEmiMin)}
                </div>
                <div className="text-sm text-gray-600">
                  to {formatCurrency(estimatedEmiMax)}
                </div>
              </div>
            </div>
          )}

          {/* Next Steps */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-semibold text-blue-900 mb-2">Next Steps:</h4>
            <ol className="list-decimal list-inside space-y-1 text-sm text-blue-800">
              <li>Check your email for loan agreement</li>
              <li>Review and sign the agreement</li>
              <li>Submit required documents</li>
              <li>Funds will be disbursed within 2-3 business days</li>
            </ol>
          </div>
        </div>
      )}

      {/* Hold Message */}
      {eligibility === 'HOLD' && (
        <div className="bg-white rounded-lg p-6">
          <p className="text-gray-700 mb-4">
            Your application is under manual review by our credit team. This typically happens when:
          </p>
          <ul className="list-disc list-inside space-y-2 text-gray-600 mb-4">
            <li>Additional verification is needed</li>
            <li>Your profile requires human assessment</li>
            <li>We need more information from you</li>
          </ul>
          <p className="text-gray-700 font-semibold">
            Expected decision time: 24-48 hours
          </p>
          <p className="text-sm text-gray-600 mt-2">
            We'll notify you via email and SMS once a decision is made.
          </p>
        </div>
      )}

      {/* Rejection Message */}
      {eligibility === 'REJECTED' && (
        <div className="bg-white rounded-lg p-6">
          <p className="text-gray-700 mb-4">
            We're unable to approve your loan application at this time. Common reasons include:
          </p>
          <ul className="list-disc list-inside space-y-2 text-gray-600 mb-4">
            <li>Income below minimum threshold for requested amount</li>
            <li>Insufficient credit history or stability signals</li>
            <li>High debt-to-income ratio</li>
          </ul>
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="font-semibold text-blue-900 mb-2">What you can do:</h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-blue-800">
              <li>Build your credit history over 3-6 months</li>
              <li>Ensure all bill payments are on time</li>
              <li>Consider adding a nominee/guarantor</li>
              <li>Reapply after improving your profile</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default LoanTermsCard;
