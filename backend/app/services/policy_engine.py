"""
Policy engine: Hard compliance rules that cannot be overridden by ML model
Enforces business rules and regulatory requirements
"""

from typing import Dict, Tuple
from app.core.config import settings

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
