"""
Trust service: Nominee/endorser framework for financial inclusion
Enables unbanked populations to access credit through trusted endorsers
"""

from typing import Dict, Tuple, Optional
from app.core.config import ENDORSER_ELIGIBILITY
import logging

logger = logging.getLogger(__name__)


class TrustService:
    """
    Manages nominee/endorser framework for trust-backed lending.
    Critical for homemakers and other thin-file borrowers.
    """
    
    ELIGIBILITY = ENDORSER_ELIGIBILITY
    
    def __init__(self, db=None):
        self.db = db
    
    def validate_endorser_eligibility(self, nominee_data: Dict) -> Tuple[bool, str]:
        """
        Check if nominated endorser meets eligibility requirements.
        
        Returns:
            (is_eligible, reason)
        """
        # Age check
        age = nominee_data.get('age')
        if not age or age < self.ELIGIBILITY['min_age']:
            return False, f"Endorser must be at least {self.ELIGIBILITY['min_age']} years old"
        
        # Relationship check
        relationship = nominee_data.get('relationship')
        if relationship not in self.ELIGIBILITY['valid_relationships']:
            return False, f"Invalid relationship. Must be one of: {self.ELIGIBILITY['valid_relationships']}"
        
        return True, "Endorser eligible"
    
    def check_endorser_existing_commitments(self, endorser_id: str) -> Tuple[bool, str]:
        """
        Check if endorser is already standing for too many loans.
        
        Max existing endorsements: 2 concurrent loans
        
        Returns:
            (can_endorse, reason)
        """
        # TODO: Query database for existing endorsements
        # For now, return True (no commitments tracked)
        return True, "Endorser has capacity"
    
    def compute_endorser_income_ratio(self, endorser_income: int, 
                                      proposed_monthly_emi: int) -> float:
        """
        Compute endorser's income relative to loan EMI.
        
        Rule: Endorser income must be >= 3x monthly EMI
        
        Returns:
            income_to_emi_ratio (float)
        """
        if proposed_monthly_emi <= 0:
            return 0.0
        
        return endorser_income / proposed_monthly_emi
    
    def validate_collateral(self, collateral_data: Dict) -> Tuple[bool, float]:
        """
        Validate and value collateral provided by endorser.
        
        Returns:
            (is_valid, adjusted_value)
        """
        if not collateral_data:
            return False, 0.0
        
        collateral_type = collateral_data.get('type')
        stated_value = collateral_data.get('value', 0)
        
        if not collateral_type or not stated_value:
            return False, 0.0
        
        # Get discount factor (conservative valuation)
        discount = self.ELIGIBILITY['collateral_discount_factors'].get(
            collateral_type, 0.5
        )
        
        adjusted_value = stated_value * discount
        
        return True, adjusted_value
    
    def apply_trust_adjustment(self, base_probability_of_default: float, 
                              nominee_data: Dict, 
                              collateral_verified: bool) -> float:
        """
        Adjust probability of default based on nominee/trust quality.
        
        This CANNOT override the floor (5%) or ceiling (95%) of PD.
        Maximum adjustment: ±15 percentage points.
        
        Args:
            base_probability_of_default: PD from ML model (0.0-1.0)
            nominee_data: Dictionary with endorser details
            collateral_verified: Whether collateral is verified
        
        Returns:
            adjusted_probability_of_default (0.05-0.95)
        """
        adjustment = 0.0
        
        # Collateral verification: -5pp
        if collateral_verified:
            adjustment -= 0.05
        
        # Income ratio: up to -5pp
        endorser_income = nominee_data.get('monthly_income', 0)
        estimated_emi = nominee_data.get('estimated_emi', 1)
        income_ratio = self.compute_endorser_income_ratio(endorser_income, estimated_emi)
        
        if income_ratio >= 5.0:
            adjustment -= 0.05
        elif income_ratio >= 3.0:
            adjustment -= 0.02
        
        # Relationship factor: up to -2pp
        relationship = nominee_data.get('relationship')
        if relationship in ['spouse', 'parent']:
            adjustment -= 0.02
        
        # Cap adjustment
        adjustment = max(-0.15, min(0.15, adjustment))
        
        # Apply adjustment and enforce floors/ceiling
        adjusted_pd = base_probability_of_default + adjustment
        adjusted_pd = max(0.05, min(0.95, adjusted_pd))
        
        return adjusted_pd
    
    def compute_loan_exposure_cap_with_nominee(self, 
                                               nominee_quality: Dict) -> int:
        """
        Determine maximum loan exposure based on nominee tier.
        
        Tiers:
        - No nominee: ₹25,000 max
        - Income proof only: ₹1,00,000 max
        - Verified collateral: ₹5,00,000 max
        - High-value collateral: ₹10,00,000 max
        
        Returns:
            max_loan_amount (int)
        """
        if not nominee_quality:
            return 25000
        
        collateral_verified = nominee_quality.get('collateral_verified', False)
        collateral_value = nominee_quality.get('collateral_adjusted_value', 0)
        has_income_proof = nominee_quality.get('has_income_proof', False)
        
        if not has_income_proof:
            return 25000
        
        if not collateral_verified:
            return 100000
        
        if collateral_value >= 500000:
            return 1000000
        
        return 500000
    
    def create_endorsement_record(self, application_id: str, 
                                 endorser_data: Dict) -> Dict:
        """
        Create endorsement record in database.
        
        Returns:
            endorsement_record_dict
        """
        # TODO: Insert into nominees table
        return {
            'endorsement_id': 'tmp_id',
            'application_id': application_id,
            'endorser_name': endorser_data.get('full_name'),
            'relationship': endorser_data.get('relationship'),
            'status': 'under_verification'
        }
