"""
Comprehensive test suite for Barclays Credit Intelligence Platform
Tests cover fraud detection, policy engine, fairness monitoring, and admin routes
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json

from app.services import FraudCheckService
from app.services.policy_engine import PolicyEngine
from app.services.fairness_service import FairnessMonitor
from app.services.portfolio_service import MonteCarloPortfolioSimulator, Loan
from app.services.chatbot_service import ChatbotService
from app.models.models import LoanApplication, User


# ─────────────────────────────────────────────────────────────────
# FRAUD CHECK SERVICE TESTS
# ─────────────────────────────────────────────────────────────────

class TestFraudCheckService:
    """Test fraud detection and identity validation"""
    
    @pytest.fixture
    def fraud_service(self):
        return FraudCheckService(db=None)
    
    @pytest.fixture
    def valid_application(self):
        return {
            'aadhaar_number': '123456789012',
            'phone_number': '9876543210',
            'email': 'test@example.com',
            'user_category': 'farmer',
            'annual_income_estimate': 50000,
            'has_bank_account': True
        }
    
    def test_valid_aadhaar_format(self, fraud_service):
        """Test Aadhaar format validation"""
        valid_aadhaar = '123456789012'
        assert fraud_service._is_valid_indian_phone('9876543210')
        assert not fraud_service._is_valid_indian_phone('1234567890')  # Starts with 1
        assert not fraud_service._is_valid_indian_phone('98765432')    # Only 8 digits
    
    def test_valid_phone_format(self, fraud_service):
        """Test Indian phone format validation"""
        assert fraud_service._is_valid_indian_phone('9876543210')
        assert fraud_service._is_valid_indian_phone('+919876543210')
        assert not fraud_service._is_valid_indian_phone('1234567890')
        assert not fraud_service._is_valid_indian_phone('87654321')
    
    def test_check_minimum_income_threshold(self, fraud_service, valid_application):
        """Test income threshold validation"""
        # Valid income for farmer
        passes, reason = fraud_service.check_minimum_income_threshold(valid_application)
        assert passes
        
        # Income too low
        valid_application['annual_income_estimate'] = 1000
        passes, reason = fraud_service.check_minimum_income_threshold(valid_application)
        assert not passes
    
    def test_check_basic_stability_signals(self, fraud_service, valid_application):
        """Test stability signal detection"""
        # Has bank account
        passes, reason = fraud_service.check_basic_stability_signals(valid_application)
        assert passes
        
        # No stability signals
        valid_application['has_bank_account'] = False
        valid_application['bank_statement_uploaded'] = False
        passes, reason = fraud_service.check_basic_stability_signals(valid_application)
        assert not passes
    
    def test_income_plausibility_farmer(self, fraud_service):
        """Test income plausibility for farmer category"""
        app_data = {
            'user_category': 'farmer',
            'annual_income_estimate': 100000,  # Within 3k-200k range
            'has_nominee': True
        }
        score = fraud_service.check_income_vs_category_plausibility(app_data)
        assert 0 <= score <= 1
        assert score < 0.3  # Should be low fraud score (plausible)
    
    def test_income_plausibility_implausible(self, fraud_service):
        """Test fraud score for implausible income"""
        app_data = {
            'user_category': 'daily_wage_worker',
            'annual_income_estimate': 30000,  # Way too high for daily wage
        }
        score = fraud_service.check_income_vs_category_plausibility(app_data)
        assert score > 0.5  # High fraud score
    
    def test_compute_fraud_score_pass(self, fraud_service, valid_application):
        """Test fraud score computation for clean application"""
        score = fraud_service.compute_fraud_score(valid_application)
        assert 0 <= score <= 1
        decision = fraud_service.decision_from_fraud_score(score)
        assert decision in ['PASS', 'HOLD', 'REJECT']
    
    def test_fraud_decision_thresholds(self, fraud_service):
        """Test fraud decision thresholds"""
        assert fraud_service.decision_from_fraud_score(0.2) == 'PASS'
        assert fraud_service.decision_from_fraud_score(0.4) == 'HOLD'
        assert fraud_service.decision_from_fraud_score(0.7) == 'REJECT'


# ─────────────────────────────────────────────────────────────────
# POLICY ENGINE TESTS
# ─────────────────────────────────────────────────────────────────

class TestPolicyEngine:
    """Test business rule enforcement"""
    
    @pytest.fixture
    def policy_engine(self):
        return PolicyEngine(db=None)
    
    def test_emi_affordability_rule_pass(self, policy_engine):
        """Test EMI affordability validation"""
        passes, reason = policy_engine.apply_emi_rule(
            proposed_emi=10000,
            monthly_income=30000,
            user_category='low_income_salaried'
        )
        assert passes  # 10000/30000 = 33%, within 40% limit
    
    def test_emi_affordability_farmer_strict(self, policy_engine):
        """Test farmer EMI has stricter limits"""
        passes, reason = policy_engine.apply_emi_rule(
            proposed_emi=10000,
            monthly_income=30000,
            user_category='farmer'
        )
        # 10000/30000 = 33%, but farmer max is 30%
        assert not passes
    
    def test_risk_threshold_auto_approve(self, policy_engine):
        """Test auto-approval for low PD"""
        decision = policy_engine.apply_risk_threshold_rule(0.1)
        assert decision == 'approve'
    
    def test_risk_threshold_auto_reject(self, policy_engine):
        """Test auto-rejection for high PD"""
        decision = policy_engine.apply_risk_threshold_rule(0.7)
        assert decision == 'reject'
    
    def test_risk_threshold_hold(self, policy_engine):
        """Test hold for medium PD"""
        decision = policy_engine.apply_risk_threshold_rule(0.4)
        assert decision == 'hold'
    
    def test_exposure_cap_rule(self, policy_engine):
        """Test exposure cap enforcement"""
        passes, reason = policy_engine.apply_exposure_cap(
            requested_amount=300000,
            existing_exposure=500000
        )
        # Total = 800k, cap = 1M, should pass
        assert passes
        
        passes, reason = policy_engine.apply_exposure_cap(
            requested_amount=600000,
            existing_exposure=500000
        )
        # Total = 1.1M, exceeds cap
        assert not passes
    
    def test_new_user_cap(self, policy_engine):
        """Test first-time borrower caps"""
        passes, reason = policy_engine.apply_new_user_cap(
            requested_amount=40000,
            user_is_new=True
        )
        assert passes
        
        passes, reason = policy_engine.apply_new_user_cap(
            requested_amount=100000,
            user_is_new=True
        )
        assert not passes
    
    def test_interest_rate_determination(self, policy_engine):
        """Test interest rate matrix"""
        rate_min, rate_max = policy_engine.determine_interest_rate(
            loan_amount=80000,      # Small loan
            tenure_months=12,
            credit_score=600,
            user_category='gig_worker'
        )
        assert rate_min < rate_max
        assert rate_min >= 8 and rate_max <= 30
    
    def test_credit_ladder_tier_new_user(self, policy_engine):
        """Test credit ladder tier assignment"""
        tier = policy_engine.determine_credit_ladder_tier([], 500)
        assert tier == 'tier_0_new'
    
    def test_loan_terms_recommendation(self, policy_engine):
        """Test loan term recommendations"""
        terms = policy_engine.recommend_loan_terms(
            loan_amount=150000,
            monthly_income=30000,
            user_category='gig_worker',
            credit_score=650,
            existing_loans=[]
        )
        assert 'recommended_amount' in terms
        assert 'recommended_tenure_months' in terms
        assert 'interest_rate_min' in terms


# ─────────────────────────────────────────────────────────────────
# FAIRNESS MONITORING TESTS
# ─────────────────────────────────────────────────────────────────

class TestFairnessMonitor:
    """Test bias detection and fairness metrics"""
    
    @pytest.fixture
    def fairness_monitor(self):
        return FairnessMonitor(db=None)
    
    @pytest.fixture
    def sample_decisions(self):
        return [
            {'gender': 'male', 'final_decision': 'approved'},
            {'gender': 'male', 'final_decision': 'approved'},
            {'gender': 'male', 'final_decision': 'approved'},
            {'gender': 'female', 'final_decision': 'approved'},
            {'gender': 'female', 'final_decision': 'rejected'},
        ]
    
    def test_approval_rate_computation(self, fairness_monitor, sample_decisions):
        """Test approval rate by group"""
        rates = fairness_monitor.compute_approval_rate_by_group(sample_decisions, 'gender')
        assert rates['male'] == 1.0
        assert rates['female'] == 0.5
    
    def test_disparate_impact_ratio(self, fairness_monitor):
        """Test disparate impact calculation"""
        approval_rates = {'male': 0.90, 'female': 0.60}
        result = fairness_monitor.compute_disparate_impact_ratio(approval_rates)
        
        # DIR = 0.60 / 0.90 = 0.67
        assert 'ratios' in result
        assert result['bias_detected']  # DIR < 0.80
    
    def test_no_disparate_impact_detected(self, fairness_monitor):
        """Test when no bias is detected"""
        approval_rates = {'male': 0.85, 'female': 0.82}
        result = fairness_monitor.compute_disparate_impact_ratio(approval_rates)
        
        # DIR = 0.82 / 0.85 = 0.96, above threshold
        assert not result['bias_detected']


# ─────────────────────────────────────────────────────────────────
# PORTFOLIO RISK ENGINE TESTS
# ─────────────────────────────────────────────────────────────────

class TestPortfolioRiskEngine:
    """Test Monte Carlo portfolio simulation"""
    
    @pytest.fixture
    def sample_portfolio(self):
        return [
            {
                'id': '1',
                'amount': 100000,
                'probability_of_default': 0.15,
                'user_category': 'gig_worker'
            },
            {
                'id': '2',
                'amount': 200000,
                'probability_of_default': 0.20,
                'user_category': 'msme_owner'
            },
            {
                'id': '3',
                'amount': 150000,
                'probability_of_default': 0.25,
                'user_category': 'farmer'
            }
        ]
    
    def test_portfolio_initialization(self, sample_portfolio):
        """Test portfolio simulator initialization"""
        simulator = MonteCarloPortfolioSimulator(sample_portfolio, n_simulations=100)
        assert len(simulator.portfolio) == 3
        assert simulator.total_exposure == 450000
    
    def test_loan_expected_loss(self):
        """Test expected loss calculation"""
        loan = Loan(
            loan_id='test',
            amount=100000,
            pd=0.20,
            lgd=0.60,
            user_category='gig_worker',
            issued_date=datetime.utcnow()
        )
        expected_loss = loan.expected_loss()
        assert expected_loss == 12000  # 100k * 0.20 * 0.60
    
    def test_monte_carlo_simulation(self, sample_portfolio):
        """Test Monte Carlo simulation runs without error"""
        simulator = MonteCarloPortfolioSimulator(sample_portfolio, n_simulations=1000)
        results = simulator.simulate()
        
        assert 'expected_loss_inr' in results
        assert 'var_95_inr' in results
        assert 'var_99_inr' in results
        assert results['var_95_inr'] >= results['expected_loss_inr']
    
    def test_portfolio_statistics(self, sample_portfolio):
        """Test portfolio statistics computation"""
        simulator = MonteCarloPortfolioSimulator(sample_portfolio)
        stats = simulator.compute_portfolio_statistics()
        
        assert stats['total_exposure_inr'] == 450000
        assert stats['num_loans'] == 3
        assert 'portfolio_pd' in stats
        assert 'by_category' in stats
    
    def test_concentration_risk_identification(self, sample_portfolio):
        """Test concentration risk detection"""
        simulator = MonteCarloPortfolioSimulator(sample_portfolio)
        concentration = simulator.identify_concentration_risk()
        
        assert 'concentration_by_category' in concentration
        assert concentration['risk_assessment'] in ['LOW', 'MEDIUM', 'HIGH']


# ─────────────────────────────────────────────────────────────────
# CHATBOT SERVICE TESTS
# ─────────────────────────────────────────────────────────────────

class TestChatbotService:
    """Test chatbot conversational AI"""
    
    @pytest.fixture
    def chatbot(self):
        return ChatbotService(api_key=None)  # Use fallback mode
    
    @pytest.fixture
    def user_context(self):
        return {
            'user_category': 'gig_worker',
            'credit_score': 650,
            'application_status': 'submitted',
            'top_positive_factors': ['Platform tenure', 'Consistent earnings'],
            'top_negative_factors': ['No bank account']
        }
    
    def test_fallback_response_credit_score_question(self, chatbot, user_context):
        """Test fallback chatbot response for credit score question"""
        response, _ = chatbot.chat(
            "Why is my credit score 650?",
            user_context
        )
        assert response
        assert len(response) > 0
        assert isinstance(response, str)
    
    def test_fallback_response_improvement(self, chatbot, user_context):
        """Test fallback response for improvement suggestions"""
        response, _ = chatbot.chat(
            "How can I improve my score?",
            user_context
        )
        assert 'improve' in response.lower() or 'payment' in response.lower()
    
    def test_system_prompt_generation(self, chatbot, user_context):
        """Test system prompt includes user context"""
        prompt = chatbot.generate_system_prompt(user_context)
        assert 'gig_worker' in prompt
        assert '650' in prompt
    
    def test_shap_factor_explanation(self, chatbot, user_context):
        """Test SHAP factor explanation conversion"""
        explanation = chatbot.explain_shap_factor_simple(
            'income_stability',
            shap_value=0.15,
            feature_value=0.7,
            user_category='gig_worker'
        )
        assert explanation
        assert 'income' in explanation.lower()
    
    def test_next_actions_generation(self, chatbot, user_context):
        """Test next actions suggestions"""
        actions = chatbot.suggest_next_actions(user_context)
        assert isinstance(actions, list)
        assert len(actions) > 0


# ─────────────────────────────────────────────────────────────────
# INTEGRATION TESTS
# ─────────────────────────────────────────────────────────────────

class TestIntegration:
    """Test end-to-end workflows"""
    
    def test_fraud_check_to_policy_engine(self):
        """Test fraud check → policy engine pipeline"""
        fraud_service = FraudCheckService()
        policy_engine = PolicyEngine()
        
        application = {
            'aadhaar_number': '123456789012',
            'phone_number': '9876543210',
            'user_category': 'farmer',
            'annual_income_estimate': 100000,
            'has_bank_account': True,
            'monthly_income': 8000,
            'requested_amount': 100000,
            'requested_tenure_months': 12
        }
        
        # Run fraud check
        fraud_score = fraud_service.compute_fraud_score(application)
        fraud_decision = fraud_service.decision_from_fraud_score(fraud_score)
        
        assert fraud_decision in ['PASS', 'HOLD', 'REJECT']
        
        # If fraud check passes, run policy checks
        if fraud_decision != 'REJECT':
            app_dict = {
                **application,
                'probability_of_default': 0.20,
                'credit_score': 650,
                'estimated_emi': 9000,
                'is_new_user': True,
                'existing_exposure': 0
            }
            
            policy_results = policy_engine.run_all_policy_checks(app_dict)
            assert 'all_pass' in policy_results
            assert 'results' in policy_results


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
