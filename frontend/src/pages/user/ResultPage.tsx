import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store/store';
import { fetchScore, runSimulation } from '../../store/applicationSlice';
import CreditScoreGauge from '../../components/CreditScoreGauge';
import ShapChart from '../../components/ShapChart';
import { Shield, CheckCircle, Clock, XCircle, ArrowLeft, TrendingUp, TrendingDown } from 'lucide-react';

const ResultPage: React.FC = () => {
  const { applicationId } = useParams<{ applicationId: string }>();
  const dispatch = useDispatch<AppDispatch>();
  const { scoreResult, simulationResult, loading, error } = useSelector((s: RootState) => s.application);

  const [sliders, setSliders] = useState({ income: 0, amount: 75000, tenure: 18 });
  const [debounceTimer, setDebounceTimer] = useState<NodeJS.Timeout | null>(null);
  const score = scoreResult;
  const simScore = simulationResult;
  const displayScore = simScore?.adjusted_credit_score || score?.credit_score || 0;

  useEffect(() => {
    if (applicationId) {
      dispatch(fetchScore(applicationId));
    }
  }, [applicationId, dispatch]);

  // Initialize sliders with actual application data
  useEffect(() => {
    if (score) {
      setSliders({
        income: 0,
        amount: score.suggested_amount || 75000,
        tenure: score.suggested_tenure_months || 18,
      });
    }
  }, [score]);

  const handleSliderChange = (field: string, value: number) => {
    const newSliders = { ...sliders, [field]: value };
    setSliders(newSliders);

    // Clear existing timer
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    // Set new timer for debounced API call
    const timer = setTimeout(() => {
      if (applicationId) {
        dispatch(runSimulation({
          id: applicationId,
          data: {
            application_id: applicationId,
            adjusted_income_percentage: newSliders.income,
            adjusted_loan_amount: newSliders.amount,
            adjusted_tenure_months: newSliders.tenure,
          },
        }));
      }
    }, 800);
    
    setDebounceTimer(timer);
  };

  if (loading && !score) {
    return (
      <div className="min-h-screen bg-user-bg flex items-center justify-center">
        <p className="text-user-muted font-body">Loading your assessment...</p>
      </div>
    );
  }

  if (error || !score) {
    return (
      <div className="min-h-screen bg-user-bg flex items-center justify-center px-6">
        <div className="max-w-md w-full p-4 bg-white border border-red-200 rounded-input text-red-600 text-sm font-body">
          {typeof error === 'string' ? error : 'Score is not available yet. Please return later after processing completes.'}
        </div>
      </div>
    );
  }

  const decisionBanner = () => {
    const eligibility = simScore?.adjusted_eligibility || score.eligibility;
    if (eligibility === 'APPROVED') return { gradient: 'from-emerald-800 to-emerald-500', icon: <CheckCircle size={24} />, title: 'Congratulations — Your loan has been approved', text: 'You will receive your funds within 2-3 business days.' };
    if (eligibility === 'REJECTED') return { gradient: 'from-red-900 to-red-500', icon: <XCircle size={24} />, title: 'We\'re unable to offer a loan at this time', text: 'You can appeal this decision or try again after improving your profile.' };
    return { gradient: 'from-amber-800 to-amber-500', icon: <Clock size={24} />, title: 'Under Review — A specialist will contact you within 24 hours', text: 'Your application is being reviewed by our risk assessment team.' };
  };

  const banner = decisionBanner();
  const shapPositive = score.top_positive_factors.map((f, i) => ({ feature: f, value: 0.12 - i * 0.02 }));
  const shapNegative = score.top_negative_factors.map((f, i) => ({ feature: f, value: 0.10 - i * 0.02 }));

  const breakdownPillars = [
    { label: 'Income Stability', score: score.income_stability_score, max: 25, weight: '25%' },
    { label: 'Repayment Capacity', score: score.repayment_capacity_score, max: 30, weight: '30%' },
    { label: 'Spending Patterns', score: score.spending_data_score, max: 15, weight: '15%' },
    { label: 'Profile Completeness', score: score.profile_completeness_score, max: 10, weight: '10%' },
    { label: 'Alternative Data', score: score.alternative_data_score, max: 20, weight: '20%' },
  ];

  return (
    <div className="min-h-screen bg-user-bg">
      <header className="bg-white border-b border-user-border px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield size={20} className="text-barclays-gold" />
          <span className="font-display font-semibold text-barclays-navy">Credit Assessment</span>
        </div>
        <Link to="/" className="flex items-center gap-1 text-sm text-user-muted hover:text-barclays-navy transition-colors font-body">
          <ArrowLeft size={14} /> Home
        </Link>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-8 space-y-6">
        {/* Score Hero */}
        <div className="bg-white rounded-card shadow-card-user p-8 text-center">
          <CreditScoreGauge score={displayScore} />
        </div>

        {/* Decision Banner */}
        <div className={`bg-gradient-to-r ${banner.gradient} rounded-card p-6 text-white flex items-center gap-4`}>
          {banner.icon}
          <div>
            <h2 className="font-display font-semibold text-lg">{banner.title}</h2>
            <p className="text-sm opacity-80 mt-1 font-body">{banner.text}</p>
          </div>
        </div>

        {/* Score Breakdown */}
        <div className="bg-white rounded-card shadow-card-user p-6">
          <h3 className="text-lg font-display font-semibold text-user-text mb-4">How your score was calculated</h3>
          <div className="space-y-3">
            {breakdownPillars.map((pillar, i) => (
              <div key={pillar.label} className="flex items-center gap-3" style={{ animationDelay: `${i * 200}ms` }}>
                <span className="text-sm text-user-muted w-40 shrink-0 font-body">{pillar.label} ({pillar.weight})</span>
                <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full rounded-full transition-all duration-1000 ease-smooth bg-gradient-to-r from-barclays-navy to-barclays-blue"
                    style={{ width: `${(pillar.score / pillar.max) * 100}%` }} />
                </div>
                <span className="text-sm font-data font-medium text-barclays-navy w-12 text-right">{pillar.score}/{pillar.max}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Loan Terms */}
        {score.eligibility !== 'REJECTED' && (
          <div className="bg-white rounded-card shadow-card-user p-6 border-l-4 border-barclays-navy">
            <h3 className="text-lg font-display font-semibold text-user-text mb-4">Loan Terms</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-xs text-user-muted font-body">Loan Amount</span>
                <p className="text-xl font-display font-bold text-barclays-navy">₹{(score.suggested_amount || 0).toLocaleString()}</p>
              </div>
              <div>
                <span className="text-xs text-user-muted font-body">Interest Rate</span>
                <p className="text-xl font-display font-bold text-barclays-teal">{score.interest_rate_min}% – {score.interest_rate_max}%</p>
              </div>
              <div>
                <span className="text-xs text-user-muted font-body">Tenure</span>
                <p className="text-lg font-semibold text-user-text font-body">{score.suggested_tenure_months} months</p>
              </div>
              <div>
                <span className="text-xs text-user-muted font-body">Est. EMI</span>
                <p className="text-lg font-semibold text-user-text font-body">₹{(score.estimated_emi_max || 0).toLocaleString()}/month</p>
              </div>
            </div>
          </div>
        )}

        {/* SHAP Explanation */}
        <div className="bg-white rounded-card shadow-card-user p-6">
          <h3 className="text-lg font-display font-semibold text-user-text mb-4">Key factors in your assessment</h3>
          <ShapChart positiveFactors={shapPositive} negativeFactors={shapNegative} />
          {score.shap_summary && (
            <div className="mt-4 p-4 bg-barclays-lightblue/50 border-l-3 border-barclays-blue rounded-r-lg">
              <p className="text-sm text-barclays-navy font-body leading-relaxed">{score.shap_summary}</p>
            </div>
          )}
        </div>

        {/* What-If Simulator */}
        <div className="bg-white rounded-card shadow-card-user p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={18} className="text-barclays-teal" />
            <h3 className="text-lg font-display font-semibold text-user-text">Improve your score</h3>
          </div>
          <p className="text-sm text-user-muted mb-4 font-body">
            Adjust the sliders below to see how changes would affect your credit score in real-time.
          </p>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-user-muted font-body">Monthly Income Adjustment</span>
                <span className="font-data text-barclays-navy">{sliders.income > 0 ? '+' : ''}{sliders.income}%</span>
              </div>
              <input type="range" min={-50} max={50} value={sliders.income} onChange={(e) => handleSliderChange('income', parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-barclays-navy" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-user-muted font-body">Loan Amount</span>
                <span className="font-data text-barclays-navy">₹{sliders.amount.toLocaleString()}</span>
              </div>
              <input type="range" min={5000} max={1000000} step={5000} value={sliders.amount} onChange={(e) => handleSliderChange('amount', parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-barclays-navy" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-user-muted font-body">Tenure</span>
                <span className="font-data text-barclays-navy">{sliders.tenure} months</span>
              </div>
              <input type="range" min={3} max={60} value={sliders.tenure} onChange={(e) => handleSliderChange('tenure', parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-barclays-navy" />
            </div>
          </div>
          {loading && !score && (
            <div className="mt-4 p-4 bg-gray-50 rounded-card text-center">
              <span className="text-sm text-user-muted font-body">Calculating...</span>
            </div>
          )}
          {simScore && (
            <div className="mt-4 p-4 bg-gray-50 rounded-card flex items-center justify-between animate-fade-in">
              <div className="flex items-center gap-2">
                {simScore.score_change >= 0 ? <TrendingUp size={16} className="text-risk-low" /> : <TrendingDown size={16} className="text-risk-very_high" />}
                <span className="text-sm font-body">Score would change by</span>
              </div>
              <span className={`font-data font-bold ${simScore.score_change >= 0 ? 'text-risk-low' : 'text-risk-very_high'}`}>
                {simScore.score_change > 0 ? '+' : ''}{simScore.score_change} points
              </span>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default ResultPage;
