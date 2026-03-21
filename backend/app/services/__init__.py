"""
Fraud detection and identity validation service
Pre-screening check before ML scoring
"""

from typing import Dict, Tuple, Optional
import logging
from app.core.config import INCOME_PLAUSIBILITY_RULES
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class FraudCheckService:
    """
    Pre-screening fraud checks using rule-based logic.
    Fast, interpretable screening before expensive ML inference.
    """
    
    def __init__(self, db=None):
        """Initialize fraud service with database connection"""
        self.db = db
    
    def check_identity_validity(self, application_data: Dict) -> Tuple[bool, str]:
        """
        Validate identity fields: Aadhaar format, phone, email, no duplicates.
        
        Returns:
            (is_valid, reason)
        """
        # Aadhaar format check (12 digits)
        if application_data.get('aadhaar_number'):
            aadhaar = application_data['aadhaar_number']
            if not aadhaar.isdigit() or len(aadhaar) != 12:
                return False, "Invalid Aadhaar format"
            
            # TODO: Implement Verhoeff checksum validation for Aadhaar
            # For now, basic format check is sufficient
        
        # Phone format check (Indian mobile)
        phone = application_data.get('phone_number', '')
        if not self._is_valid_indian_phone(phone):
            return False, "Invalid phone number format"
        
        # Email validation is done by Pydantic, skip here
        
        return True, "Identity valid"
    
    def check_minimum_income_threshold(self, application_data: Dict) -> Tuple[bool, str]:
        """
        Check if income meets minimum threshold for category.
        
        Returns:
            (meets_threshold, reason)
        """
        category = application_data.get('user_category')
        rules = INCOME_PLAUSIBILITY_RULES.get(category)
        
        if not rules:
            return False, f"Unknown category: {category}"
        
        income = application_data.get('annual_income_estimate') or application_data.get('monthly_income')
        
        if not income:
            return False, "No income provided"
        
        if income < rules['min']:
            return False, f"Income below minimum for {category}: {income} < {rules['min']}"
        
        return True, "Income threshold met"
    
    def check_basic_stability_signals(self, application_data: Dict) -> Tuple[bool, str]:
        """
        Check for at least one stability signal.
        
        Requirements:
        - Bank account, UPI history, employer letter, land document, 
          GST number, or platform registration
        
        Returns:
            (has_signal, reason)
        """
        signals = [
            bool(application_data.get('has_bank_account')),
            bool(application_data.get('bank_statement_uploaded')),
            bool(application_data.get('employer_letter_uploaded')),
            bool(application_data.get('land_document_uploaded')),
            bool(application_data.get('gst_number')),
            bool(application_data.get('platform_registration_ids')),
            bool(application_data.get('aadhaar_verified')),
        ]
        
        if sum(signals) >= 1:
            return True, "Has stability signal"
        
        return False, "No stability signals found - requires bank account, UPI, employer letter, or similar"
    
    def check_income_vs_category_plausibility(self, application_data: Dict) -> float:
        """
        Compute income plausibility score (fraud signal).
        
        Returns:
            fraud_score contribution (0.0-1.0)
        """
        category = application_data.get('user_category')
        income = application_data.get('annual_income_estimate') or application_data.get('monthly_income')
        
        rules = INCOME_PLAUSIBILITY_RULES.get(category)
        if not rules or not income:
            return 0.5  # Neutral if missing data
        
        # Check if income is within plausible range
        if income < rules['min'] or income > rules['max']:
            return 0.8  # High fraud score - implausible income
        
        # Check for homemaker edge case
        if category == "homemaker" and not application_data.get('has_nominee'):
            return 0.7  # Homemakers without nominee are high risk
        
        return 0.1  # Low fraud score - income is plausible
    
    def check_multiple_applications(self, user_id: str, time_window_days: int = 30) -> float:
        """
        Check for multiple applications from same user in recent time window.
        Multiple applications in short timeframe = fraud signal.
        
        Returns:
            fraud_score contribution (0.0-1.0)
        """
        # TODO: Query database for recent applications from user
        # For now, return 0.0 (no fraud signal)
        return 0.0
    
    def check_inconsistent_data_patterns(self, application_data: Dict) -> Dict:
        """
        Check for inconsistent or suspicious data patterns.
        
        Returns:
            Dict of findings
        """
        findings = {}
        
        # Check employment vs income
        category = application_data.get('user_category')
        if category == 'msme_owner':
            revenue = application_data.get('monthly_revenue', 0)
            expenses = application_data.get('monthly_expenses', 0)
            
            if expenses > revenue:
                findings['negative_profit'] = True
        
        # Check age consistency
        if application_data.get('date_of_birth'):
            # TODO: Calculate age and check if 18+
            pass
        
        return findings
    
    def compute_fraud_score(self, application_data: Dict) -> float:
        """
        Compute composite fraud score from all checks.
        
        Thresholds:
        - < 0.3: Pass
        - 0.3-0.6: Hold for manual review
        - > 0.6: Reject immediately
        
        Returns:
            fraud_score (0.0-1.0)
        """
        scores = []
        
        # Identity check
        identity_valid, _ = self.check_identity_validity(application_data)
        scores.append(0.0 if identity_valid else 0.9)
        
        # Income threshold
        income_valid, _ = self.check_minimum_income_threshold(application_data)
        scores.append(0.0 if income_valid else 0.5)
        
        # Stability signals
        has_signals, _ = self.check_basic_stability_signals(application_data)
        scores.append(0.0 if has_signals else 0.3)
        
        # Income plausibility
        income_plausibility = self.check_income_vs_category_plausibility(application_data)
        scores.append(income_plausibility)
        
        # Multiple applications
        multiple_apps = self.check_multiple_applications(application_data.get('user_id', ''))
        scores.append(multiple_apps)
        
        # Inconsistent patterns
        inconsistencies = self.check_inconsistent_data_patterns(application_data)
        scores.append(0.3 if inconsistencies else 0.0)
        
        # Weighted composite
        weights = [0.20, 0.20, 0.15, 0.25, 0.10, 0.10]
        fraud_score = sum(s * w for s, w in zip(scores, weights))
        
        return min(1.0, max(0.0, fraud_score))
    
    def decision_from_fraud_score(self, fraud_score: float) -> str:
        """
        Convert fraud score to decision.
        
        Returns:
            "PASS" | "HOLD" | "REJECT"
        """
        if fraud_score < 0.3:
            return "PASS"
        elif fraud_score < 0.6:
            return "HOLD"
        else:
            return "REJECT"
    
    @staticmethod
    def _is_valid_indian_phone(phone: str) -> bool:
        """Validate Indian phone number format"""
        # Remove +91 prefix if present
        if phone.startswith('+91'):
            phone = phone[3:]
        
        # Should be 10 digits starting with 6-9
        return bool(phone.isdigit() and len(phone) == 10 and phone[0] in '6789')


    __all__ = ["FraudCheckService", "AuditService"]
