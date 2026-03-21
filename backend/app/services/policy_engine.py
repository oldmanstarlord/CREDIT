"""
Policy engine: Hard compliance rules that cannot be overridden by ML model
Enforces business rules and regulatory requirements
"""

from typing import Dict, Tuple
from app.core.config import settings
from datetime import datetime, timedelta

import logging

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Applies hard regulatory and business rules.
    These rules CANNOT be overridden by the ML model.
    """
    
    RULES = {
        "emi_to_income_max_ratio": settings.EMI_TO_INCOME_MAX_RATIO,
        "farmer_emi_to_income_max": settings.FARMER_EMI_TO_INCOME_MAX,
        "daily_worker_emi_to_income_max": settings.DAILY_WORKER_EMI_TO_INCOME_MAX,
        "min_credit_score_for_approval": settings.MIN_CREDIT_SCORE_FOR_APPROVAL,
        "auto_reject_pd_threshold": 0.65,
        "auto_approve_pd_threshold": 0.15,
        "max_loan_without_collateral": settings.MAX_LOAN_WITHOUT_COLLATERAL,
        "max_exposure_per_user": settings.MAX_EXPOSURE_PER_USER,
        "new_user_max_loan": settings.NEW_USER_MAX_LOAN
    }
    
    # Interest rate matrix by loan size and tenure
    INTEREST_RATE_MATRIX = {
        "small_loans_up_to_1_lakh": (18, 25),      # 18–25% for ≤1 lakh
        "medium_loans_1_to_3_lakh": (12, 18),      # 12–18% for 1-3 lakh
        "large_loans_3_to_10_lakh": (10, 12),      # 10–12% for 3-10 lakh
        "premium_above_10_lakh": (8, 10)           # 8–10% for >10 lakh
    }
    
    # Credit ladder tiers
    CREDIT_LADDER = {
        "tier_0_new": {
            "label": "New User",
            "duration_months": 6,
            "max_amount": 50000,
            "interest_range": (18, 25),
            "requires_collateral": False,
        },
        "tier_1_trust_building": {
            "label": "Trust Building",
            "duration_months": 12,
            "max_amount": 500000,
            "interest_range": (12, 18),
            "requires_collateral": False,
        },
        "tier_2_established": {
            "label": "Established Borrower",
            "duration_months": 18,
            "max_amount": 1000000,
            "interest_range": (10, 14),
            "requires_collateral": False,
        },
        "tier_3_prime": {
            "label": "Prime Borrower",
            "duration_months": 36,
            "max_amount": None,  # No cap for prime borrowers
            "interest_range": (8, 10),
            "requires_collateral": True,
            "min_credit_score": 650,
        }
    }
    
    def __init__(self, db=None):
        self.db = db
    
    
    def apply_emi_rule(self, proposed_emi: int, monthly_income: int, 
                       user_category: str) -> Tuple[bool, str]:
        """
        Check if proposed EMI meets affordability rules.
        
        Rules vary by category (farmers stricter than others).
        
        Returns:
            (passes_rule, reason)
        """
        if not monthly_income or monthly_income <= 0:
            return False, "Invalid income"
        
        # Category-specific ratios
        if user_category == 'farmer':
            max_ratio = self.RULES['farmer_emi_to_income_max']
        elif user_category == 'daily_wage_worker':
            max_ratio = self.RULES['daily_worker_emi_to_income_max']
        else:
            max_ratio = self.RULES['emi_to_income_max_ratio']
        
        actual_ratio = proposed_emi / monthly_income
        
        if actual_ratio > max_ratio:
            return False, (f"EMI ({proposed_emi}) exceeds {max_ratio*100}% of income "
                          f"({monthly_income}). Ratio: {actual_ratio:.2%}")
        
        return True, "EMI affordable"
    
    def apply_risk_threshold_rule(self, probability_of_default: float) -> str:
        """
        Apply auto-approve/hold/reject thresholds based on PD.
        
        Returns:
            "approve" | "hold" | "reject"
        """
        if probability_of_default > self.RULES['auto_reject_pd_threshold']:
            return "reject"
        elif probability_of_default < self.RULES['auto_approve_pd_threshold']:
            return "approve"
        else:
            return "hold"
    
    def apply_credit_score_rule(self, credit_score: int) -> Tuple[bool, str]:
        """
        Check if credit score meets minimum threshold for any approval.
        
        Returns:
            (passes_rule, reason)
        """
        min_score = self.RULES['min_credit_score_for_approval']
        
        if credit_score < min_score:
            return False, f"Credit score ({credit_score}) below minimum ({min_score})"
        
        return True, "Credit score acceptable"
    
    def apply_exposure_cap(self, requested_amount: int, 
                          existing_exposure: int) -> Tuple[bool, str]:
        """
        Check if total exposure (existing + new) exceeds per-user cap.
        
        Returns:
            (passes_rule, reason)
        """
        total_exposure = existing_exposure + requested_amount
        max_exposure = self.RULES['max_exposure_per_user']
        
        if total_exposure > max_exposure:
            return False, (f"Total exposure ({total_exposure}) exceeds maximum "
                          f"({max_exposure}). Existing: {existing_exposure}")
        
        return True, "Exposure cap acceptable"
    
    def apply_new_user_cap(self, requested_amount: int, 
                          user_is_new: bool) -> Tuple[bool, str]:
        """
        Check if new users exceed first-loan cap.
        
        Returns:
            (passes_rule, reason)
        """
        if not user_is_new:
            return True, "Not a new user"
        
        max_first_loan = self.RULES['new_user_max_loan']
        
        if requested_amount > max_first_loan:
            return False, (f"First loan amount ({requested_amount}) exceeds "
                          f"new user cap ({max_first_loan})")
        
        return True, "New user amount acceptable"
    
    def apply_collateral_rule(self, loan_amount: int, 
                             has_collateral: bool) -> Tuple[bool, str]:
        """
        Check if loans above threshold require collateral.
        
        Returns:
            (passes_rule, reason)
        """
        max_uncollateralized = self.RULES['max_loan_without_collateral']
        
        if loan_amount > max_uncollateralized and not has_collateral:
            return False, (f"Loan amount ({loan_amount}) exceeds uncollateralized "
                          f"limit ({max_uncollateralized}). Collateral required.")
        
        return True, "Collateral requirement met"
    
    def run_all_policy_checks(self, application: Dict) -> Dict:
        """
        Run all policy engine checks and return results.
        
        Returns:
            {
                'all_pass' bool,
                'results': {
                    'emi_rule': (passes, reason),
                    'risk_threshold': (decision),
                    'credit_score': (passes, reason),
                    'exposure_cap': (passes, reason),
                    'new_user_cap': (passes, reason),
                    'collateral': (passes, reason)
                }
            }
        """
        results = {}
        
        # EMI affordability
        emi = application.get('estimated_emi', 0)
        income = application.get('monthly_income', 0)
        category = application.get('user_category', '')
        results['emi_rule'] = self.apply_emi_rule(emi, income, category)
        
        # Risk threshold
        pd = application.get('probability_of_default', 0.5)
        results['risk_threshold'] = self.apply_risk_threshold_rule(pd)
        
        # Credit score
        score = application.get('credit_score', 500)
        results['credit_score'] = self.apply_credit_score_rule(score)
        
        # Exposure cap
        requested = application.get('requested_amount', 0)
        existing = application.get('existing_exposure', 0)
        results['exposure_cap'] = self.apply_exposure_cap(requested, existing)
        
        # New user cap
        is_new = application.get('is_new_user', True)
        results['new_user_cap'] = self.apply_new_user_cap(requested, is_new)
        
        # Collateral
        has_collateral = application.get('has_nominee', False) or \
                        application.get('has_collateral', False)
        results['collateral'] = self.apply_collateral_rule(requested, has_collateral)
        
        # Summary
        checks_passed = sum(1 for r in results.values() 
                          if isinstance(r, tuple) and r[0] == True)
        total_checks = sum(1 for r in results.values() 
                          if isinstance(r, tuple))
        
        all_pass = checks_passed == total_checks
        
        return {
            'all_pass': all_pass,
            'checks_passed': checks_passed,
            'total_checks': total_checks,
            'results': results
        }
    
    def determine_interest_rate(self, loan_amount: int, tenure_months: int, 
                               credit_score: int, user_category: str) -> Tuple[float, float]:
        """
        Determine interest rate range based on loan amount, tenure, and credit score.
        
        Returns:
            (min_rate, max_rate) as percentages
        """
        # Base rate from loan size
        if loan_amount <= 100000:
            base_range = self.INTEREST_RATE_MATRIX['small_loans_up_to_1_lakh']
        elif loan_amount <= 300000:
            base_range = self.INTEREST_RATE_MATRIX['medium_loans_1_to_3_lakh']
        elif loan_amount <= 1000000:
            base_range = self.INTEREST_RATE_MATRIX['large_loans_3_to_10_lakh']
        else:
            base_range = self.INTEREST_RATE_MATRIX['premium_above_10_lakh']
        
        # Adjust for tenure (shorter tenure = higher rate)
        tenure_multiplier = min(1.0, tenure_months / 36)  # 36 months = 1.0
        rate_spread = base_range[1] - base_range[0]
        tenure_adjustment = rate_spread * (1 - tenure_multiplier) * 0.3  # 30% impact
        
        # Adjust for credit score (higher score = lower rate)
        score_multiplier = min(1.0, max(0.0, (credit_score - 500) / 350))  # 500-850 → 0-1
        score_adjustment = -rate_spread * score_multiplier * 0.3  # 30% impact
        
        # Category adjustment
        category_adjustment = 0
        if user_category == 'farmer':
            category_adjustment = 2.0  # Farmers pay 2% more due to seasonal risk
        elif user_category == 'daily_wage_worker':
            category_adjustment = 1.5  # Daily wage workers pay 1.5% more
        
        min_rate = base_range[0] + tenure_adjustment + score_adjustment + category_adjustment
        max_rate = base_range[1] + tenure_adjustment + score_adjustment + category_adjustment
        
        return float(round(min_rate, 2)), float(round(max_rate, 2))
    
    def determine_credit_ladder_tier(self, existing_loans: list, 
                                    credit_score: int) -> str:
        """
        Determine which credit ladder tier a user belongs to based on history.
        
        Returns:
            tier name (tier_0_new, tier_1_trust_building, etc.)
        """
        if not existing_loans:
            return "tier_0_new"
        
        # Check time since first loan and repayment history
        first_loan_date = min(loan.get('created_at', datetime.utcnow()) 
                             for loan in existing_loans)
        months_since_first = (datetime.utcnow() - first_loan_date).days / 30
        
        # Count on-time repayments
        on_time_count = sum(1 for loan in existing_loans 
                          if loan.get('repayment_status') == 'completed')
        total_count = len(existing_loans)
        on_time_rate = on_time_count / total_count if total_count > 0 else 0
        
        # Tier logic
        if months_since_first < 6:
            return "tier_0_new"
        elif months_since_first < 18 and on_time_rate >= 0.8:
            return "tier_1_trust_building"
        elif months_since_first >= 18 and on_time_rate >= 0.9 and credit_score >= 600:
            return "tier_2_established"
        elif credit_score >= 650 and on_time_rate >= 0.95:
            return "tier_3_prime"
        else:
            return "tier_1_trust_building"
    
    def recommend_loan_terms(self, loan_amount: int, monthly_income: int,
                            user_category: str, credit_score: int,
                            existing_loans: list = None) -> Dict:
        """
        Recommend loan terms based on applicant profile.
        
        Returns:
            {
                'recommended_amount': int,
                'recommended_tenure_months': int,
                'interest_rate_min': float,
                'interest_rate_max': float,
                'estimated_emi_min': float,
                'estimated_emi_max': float,
                'credit_tier': str,
                'reasoning': str
            }
        """
        if existing_loans is None:
            existing_loans = []
        
        # Determine credit tier
        tier = self.determine_credit_ladder_tier(existing_loans, credit_score)
        tier_info = self.CREDIT_LADDER[tier]
        
        # Cap amount by tier
        max_tier_amount = tier_info['max_amount']
        recommended_amount = min(loan_amount, max_tier_amount) if max_tier_amount else loan_amount
        
        # Recommend tenure based on category and amount
        if user_category == 'farmer':
            # Farmers use seasonal repayment, shorter tenure
            recommended_tenure = 12
        elif user_category == 'daily_wage_worker':
            # Daily workers need short tenure due to income volatility
            recommended_tenure = 12
        elif user_category == 'gig_worker':
            # Gig workers medium tenure
            recommended_tenure = 18
        elif user_category == 'msme_owner':
            # MSME can support longer tenure
            recommended_tenure = 24
        else:
            recommended_tenure = 18  # default
        
        # Get interest rates
        rate_min, rate_max = self.determine_interest_rate(
            recommended_amount, recommended_tenure, credit_score, user_category
        )
        
        # Calculate EMI
        monthly_rate_min = rate_min / 100 / 12
        monthly_rate_max = rate_max / 100 / 12
        
        emi_min = (recommended_amount * monthly_rate_min * (1 + monthly_rate_min)**recommended_tenure) / \
                  ((1 + monthly_rate_min)**recommended_tenure - 1)
        emi_max = (recommended_amount * monthly_rate_max * (1 + monthly_rate_max)**recommended_tenure) / \
                  ((1 + monthly_rate_max)**recommended_tenure - 1)
        
        # Verify EMI is affordable
        emi_ratio = emi_max / monthly_income if monthly_income > 0 else 0
        category_max_ratio = {
            'farmer': settings.FARMER_EMI_TO_INCOME_MAX,
            'daily_wage_worker': settings.DAILY_WORKER_EMI_TO_INCOME_MAX,
        }.get(user_category, settings.EMI_TO_INCOME_MAX_RATIO)
        
        if emi_ratio > category_max_ratio:
            # Adjust amount down
            target_emi = monthly_income * category_max_ratio
            recommended_amount = int(target_emi * 12 / rate_max * 100)
            emi_min = target_emi * 0.95
            emi_max = target_emi
        
        return {
            'recommended_amount': recommended_amount,
            'recommended_tenure_months': recommended_tenure,
            'interest_rate_min': rate_min,
            'interest_rate_max': rate_max,
            'estimated_emi_min': round(emi_min, 2),
            'estimated_emi_max': round(emi_max, 2),
            'credit_tier': tier,
            'tier_label': tier_info['label'],
            'reasoning': f"Based on {tier_info['label']} status with {credit_score} credit score"
        }
