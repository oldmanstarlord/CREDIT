"""
ML Feature Engineering Pipeline
Transforms raw application data into model-ready features for XGBoost scoring
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Comprehensive feature engineering for credit scoring.
    Handles all user categories with category-specific features.
    """
    
    def __init__(self):
        self.scaler_fitted = False
        self.categorical_features = []
        self.numerical_features = []
    
    def engineer_all_features(self, application_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Main feature engineering pipeline.
        
        Processes raw application data into 50+ features for ML model.
        
        Args:
            application_data: Raw application dictionary
        
        Returns:
            Dictionary of feature_name: feature_value pairs
        """
        features = {}
        
        # Standard ratio features
        features.update(self.engineer_standard_features(application_data))
        
        # Alternative behavioral features
        features.update(self.engineer_alternative_features(application_data))
        
        # Category-specific features
        category = application_data.get('user_category')
        if category == 'farmer':
            features.update(self.engineer_farmer_features(application_data))
        elif category == 'daily_wage_worker':
            features.update(self.engineer_daily_worker_features(application_data))
        elif category == 'gig_worker':
            features.update(self.engineer_gig_worker_features(application_data))
        elif category == 'msme_owner':
            features.update(self.engineer_msme_features(application_data))
        elif category == 'homemaker':
            features.update(self.engineer_homemaker_features(application_data))
        elif category == 'low_income_salaried':
            features.update(self.engineer_salaried_features(application_data))
        
        # Trust framework features
        features.update(self.engineer_trust_features(application_data))
        
        # Demographic features (for monitoring, NOT for scoring)
        # Store separately and never pass to model
        
        return features
    
    def engineer_standard_features(self, data: Dict) -> Dict[str, float]:
        """Standard credit scoring ratio features"""
        features = {}
        
        # Income-based ratios
        monthly_income = data.get('monthly_income') or data.get('annual_income_estimate', 0) / 12
        
        if monthly_income > 0:
            features['monthly_income'] = float(monthly_income)
            features['income_stability'] = float(
                1 - (data.get('income_std', 0) / (monthly_income + 1))
            )
            features['income_stability'] = max(0, min(1, features['income_stability']))
        
        # Loan request ratios
        requested_amount = data.get('requested_amount', 0)
        requested_emi = self._estimate_monthly_emi(
            requested_amount, 
            data.get('requested_tenure_months', 12)
        )
        
        if monthly_income > 0:
            features['loan_to_income_ratio'] = requested_amount / (monthly_income * 12)
            features['emi_to_income_ratio'] = requested_emi / monthly_income
        
        # Demographic
        features['age_at_application'] = self._calculate_age(
            data.get('date_of_birth')
        )
        
        # Account status
        features['has_bank_account'] = float(data.get('has_bank_account', False))
        features['has_upi_history'] = float(data.get('has_upi_history', False))
        
        return features
    
    def engineer_alternative_features(self, data: Dict) -> Dict[str, float]:
        """
        Alternative data features crucial for unbanked populations.
        These replace traditional credit history.
        """
        features = {}
        
        # Transaction consistency
        features['transaction_consistency'] = data.get('transaction_consistency', 0.5)
        
        # Bill payment regularity (utility, phone, rent)
        electricity_regularity = data.get('electricity_payment_regularity', 0.5)
        phone_regularity = data.get('phone_payment_regularity', 0.5)
        rent_regularity = data.get('rent_payment_regularity', 0.5)
        
        features['utility_payment_score'] = (
            electricity_regularity * 0.4 +
            phone_regularity * 0.3 +
            rent_regularity * 0.3
        )
        
        # Savings buffer (emergency fund)
        avg_savings = data.get('avg_monthly_savings', 0)
        monthly_expenses = data.get('monthly_expenses', 1)
        features['savings_buffer_ratio'] = avg_savings / (monthly_expenses + 1)
        features['savings_buffer_ratio'] = max(0, min(10, features['savings_buffer_ratio']))
        
        # Spending pattern
        essential_spending = data.get('essential_spending', 0)
        total_spending = data.get('total_spending', essential_spending + 1)
        features['spending_pattern_ratio'] = essential_spending / (total_spending + 1)
        
        # Cash flow volatility
        monthly_incomes = data.get('monthly_incomes_history', [])
        if len(monthly_incomes) > 1:
            cashflow_cv = np.std(monthly_incomes) / (np.mean(monthly_incomes) + 1)
            features['cash_flow_volatility'] = min(10, max(0, cashflow_cv))
        else:
            features['cash_flow_volatility'] = 0.5
        
        # Document verification
        features['has_verified_documents'] = float(
            data.get('docs_verified', False)
        )
        
        return features
    
    def engineer_farmer_features(self, data: Dict) -> Dict[str, float]:
        """Farmer-specific features"""
        features = {}
        
        # Land characteristics
        land_acres = data.get('land_size', 0)
        features['land_size'] = float(land_acres)
        
        # Assume ₹2,00,000 per acre as base value (varies by region)
        region_price = data.get('region_land_price_per_acre', 200000)
        features['land_value_proxy'] = float(land_acres * region_price)
        
        # Seasonal income indicator
        features['seasonal_income_flag'] = 1.0
        
        # Crop-specific income multiplier (from mapping, e.g., sugarcane = 4.0x)
        crop_type = data.get('crop_type', 'rice')
        from app.core.config import CROP_SEASON_MAP
        multiplier = CROP_SEASON_MAP.get(crop_type, {}).get('income_multiplier', 2.5)
        features['harvest_income_multiplier'] = float(multiplier)
        
        # Irrigation quality (better irrigation = better income)
        irrigation_type = data.get('irrigation_type', 'rainfed')
        irrigation_score = {'rainfed': 0.5, 'canal': 0.7, 'borewell': 0.85}.get(
            irrigation_type, 0.5
        )
        features['irrigation_quality_score'] = float(irrigation_score)
        
        # Has Kisan Credit Card (good signal)
        features['has_kcc'] = float(bool(data.get('kisan_credit_card_number')))
        
        return features
    
    def engineer_daily_worker_features(self, data: Dict) -> Dict[str, float]:
        """Daily wage worker-specific features"""
        features = {}
        
        daily_earnings = data.get('average_daily_earnings', 0)
        days_per_month = data.get('days_worked_per_month', 20)
        
        estimated_monthly = daily_earnings * days_per_month
        features['estimated_monthly_income'] = float(estimated_monthly)
        
        # Income stability based on day regularity
        features['income_stability_score'] = days_per_month / 30
        
        # Work consistency (self-reported)
        consistency = data.get('work_consistency', 'irregular')
        consistency_scores = {'regular': 0.9, 'irregular': 0.5, 'seasonal': 0.4}
        features['work_consistency_score'] = float(
            consistency_scores.get(consistency, 0.5)
        )
        
        return features
    
    def engineer_gig_worker_features(self, data: Dict) -> Dict[str, float]:
        """Gig worker-specific features"""
        features = {}
        
        # Platform trust scoring
        from app.core.config import PLATFORM_TRUST_SCORES
        platforms = data.get('platforms', [])
        if platforms:
            platform_scores = [
                PLATFORM_TRUST_SCORES.get(p.lower(), 0.3) for p in platforms
            ]
            features['platform_trust_score'] = float(max(platform_scores))
            features['num_platforms'] = float(len(platforms))
        else:
            features['platform_trust_score'] = 0.3
            features['num_platforms'] = 0.0
        
        # Weekly income variability
        weekly_incomes = data.get('weekly_incomes_history', [])
        if len(weekly_incomes) > 1:
            weekly_cv = np.std(weekly_incomes) / (np.mean(weekly_incomes) + 1)
            features['weekly_income_cv'] = float(min(5, max(0, weekly_cv)))
        else:
            features['weekly_income_cv'] = 0.5
        
        # Platform tenure (longer = more stable)
        months_on_platform = data.get('months_on_platform', 0)
        features['platform_tenure_score'] = min(1.0, months_on_platform / 24)
        
        # Active day ratio
        active_days = data.get('active_days_per_week', 7)
        features['active_day_ratio'] = active_days / 7
        
        return features
    
    def engineer_msme_features(self, data: Dict) -> Dict[str, float]:
        """MSME owner-specific features"""
        features = {}
        
        revenue = data.get('monthly_revenue', 0)
        expenses = data.get('monthly_expenses', 0)
        
        features['monthly_revenue'] = float(revenue)
        features['monthly_expenses'] = float(expenses)
        
        # Profit margin
        if revenue > 0:
            features['profit_margin'] = (revenue - expenses) / revenue
        else:
            features['profit_margin'] = 0.0
        
        # Expense ratio
        features['expense_to_revenue_ratio'] = expenses / (revenue + 1)
        
        # Revenue growth (if historical data available)
        monthly_revenues = data.get('monthly_revenues_history', [])
        if len(monthly_revenues) >= 3:
            # Linear regression slope
            x = np.arange(len(monthly_revenues))
            y = np.array(monthly_revenues)
            slope = np.polyfit(x, y, 1)[0]
            mean_revenue = np.mean(y)
            growth_rate = slope / (mean_revenue + 1)
            features['revenue_growth_trend'] = float(min(2, max(-1, growth_rate)))
        else:
            features['revenue_growth_trend'] = 0.0
        
        # Cash flow volatility
        if len(monthly_revenues) > 1:
            revenue_cv = np.std(monthly_revenues) / (np.mean(monthly_revenues) + 1)
            features['cash_flow_volatility'] = float(min(5, max(0, revenue_cv)))
        
        # Formalisation signals
        features['has_gst'] = float(bool(data.get('gst_registration_number')))
        features['has_udyam'] = float(bool(data.get('udyam_registration_number')))
        features['is_formalized'] = float(
            bool(data.get('gst_registration_number')) or 
            bool(data.get('udyam_registration_number'))
        )
        
        # Business age (longer = more stable)
        business_months = data.get('business_age_months', 0)
        features['business_age_score'] = min(1.0, business_months / 36)
        
        return features
    
    def engineer_homemaker_features(self, data: Dict) -> Dict[str, float]:
        """Homemaker-specific features (very limited direct features)"""
        features = {}
        
        # Homemakers rely on household/nominee income
        household_income = data.get('household_monthly_income', 0)
        features['household_income'] = float(household_income)
        
        # Family dependencies
        dependents = data.get('number_of_dependents', 0)
        features['number_of_dependents'] = float(dependents)
        
        # Income per dependent (capacity indicator)
        features['income_per_dependent'] = household_income / (dependents + 1)
        
        return features
    
    def engineer_salaried_features(self, data: Dict) -> Dict[str, float]:
        """Salaried worker-specific features"""
        features = {}
        
        monthly_salary = data.get('monthly_salary_net', 0)
        features['monthly_salary'] = float(monthly_salary)
        
        # Employment tenure (longer = more stable)
        tenure_months = data.get('employment_tenure_months', 0)
        features['employment_tenure_score'] = min(1.0, tenure_months / 36)
        
        # Employment type formalization
        emp_type = data.get('employer_type', 'private')
        type_score = {
            'govt': 0.95,
            'private': 0.75,
            'ngo': 0.70,
            'informal': 0.40
        }.get(emp_type, 0.50)
        features['employment_formalization_score'] = float(type_score)
        
        # Has salary account (good signal)
        features['salary_to_account'] = float(
            data.get('salary_credited_to_bank', False)
        )
        
        return features
    
    def engineer_trust_features(self, data: Dict) -> Dict[str, float]:
        """Trust framework (nominee) features"""
        features = {}
        
        has_nominee = data.get('has_nominee', False)
        features['has_nominee'] = float(has_nominee)
        
        if has_nominee:
            nominee = data.get('nominee_data', {})
            
            # Nominee income ratio
            nominee_income = nominee.get('monthly_income', 0)
            monthly_income = data.get('monthly_income', 1)
            features['nominee_income_ratio'] = nominee_income / (monthly_income + 1)
            
            # Collateral verification
            features['has_verified_collateral'] = float(
                nominee.get('collateral_verified', False)
            )
            
            # Collateral value
            collateral_value = nominee.get('collateral_adjusted_value', 0)
            features['collateral_value'] = float(collateral_value)
            
            # Relationship type (encode)
            relationship = nominee.get('relationship', 'other')
            relation_score = {
                'spouse': 0.9,
                'parent': 0.85,
                'sibling': 0.70,
                'employer': 0.65,
                'registered_microfinance_agent': 0.60,
                'community_leader': 0.55,
                'other': 0.30
            }.get(relationship, 0.30)
            features['nominee_relationship_score'] = float(relation_score)
        
        return features
    
    @staticmethod
    def _estimate_monthly_emi(principal: int, tenure_months: int, 
                             annual_rate: float = 0.18) -> float:
        """
        Estimate monthly EMI (Equated Monthly Installment)
        Formula: EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
        where P=principal, r=monthly_rate, n=months
        """
        if principal <= 0 or tenure_months <= 0:
            return 0.0
        
        monthly_rate = annual_rate / 12
        numerator = principal * monthly_rate * (1 + monthly_rate) ** tenure_months
        denominator = (1 + monthly_rate) ** tenure_months - 1
        
        return numerator / denominator
    
    @staticmethod
    def _calculate_age(date_of_birth_str: Optional[str]) -> int:
        """Calculate age from DOB"""
        if not date_of_birth_str:
            return 0
        
        try:
            dob = pd.to_datetime(date_of_birth_str)
            age = (datetime.now() - dob).days // 365
            return max(0, age)
        except:
            return 0
