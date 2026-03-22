"""
Pydantic schemas for request/response validation and documentation
"""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List, Dict, Any, Generic, TypeVar, Union
from datetime import datetime, date, time
from enum import Enum


# ─── AUTH SCHEMAS ──────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    phone_number: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=8)
    full_name: str
    date_of_birth: Optional[datetime] = None
    aadhaar_number: Optional[str] = None
    user_category: Optional[str] = None


class UserLoginRequest(BaseModel):
    """User login request"""
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    password: str
    
    @field_validator('email', 'phone_number')
    def at_least_one_identifier(cls, v, info):
        if not v and not info.data.get('phone_number') and not info.data.get('email'):
            raise ValueError("Either email or phone_number required")
        return v


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


# ─── USER SCHEMAS ──────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    """User profile response"""
    id: str
    email: str
    phone_number: str
    full_name: str
    role: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    aadhaar_number: Optional[str] = None
    user_category: Optional[str] = None
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """User profile update"""
    full_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    phone_number: Optional[str] = None


# ─── LOAN APPLICATION SCHEMAS ──────────────────────────────────────────────

class StepOnePersonalDetails(BaseModel):
    """Step 1: Personal details"""
    full_name: str = Field(..., min_length=2, max_length=255)
    date_of_birth: datetime
    gender: Optional[str] = None
    phone_number: str = Field(..., pattern=r'^(?:\+91)?[6-9]\d{9}$')  # Indian mobile
    email: EmailStr
    aadhaar_number: Optional[str] = Field(None, pattern=r'^\d{12}$')


class StepTwoUserCategory(BaseModel):
    """Step 2: Category selection"""
    user_category: str = Field(..., description="farmer, daily_wage_worker, gig_worker, msme_owner, homemaker, low_income_salaried")


class StepThreeFarmerData(BaseModel):
    """Step 3: Farmer-specific data"""
    land_size: float = Field(..., gt=0, description="in acres or hectares")
    land_location_state: str
    land_location_district: str
    land_location_village: Optional[str] = None
    crop_type: str  # wheat, rice, sugarcane, cotton, vegetables
    irrigation_type: str  # rainfed, canal, borewell
    expected_harvest_months: List[int]  # 1-12
    annual_income_estimate: int = Field(..., gt=0)
    dependent_family_members: int = Field(default=0, ge=0)
    kisan_credit_card_number: Optional[str] = None


class StepThreeDailyWorkerData(BaseModel):
    """Step 3: Daily wage worker-specific data"""
    occupation_type: str
    average_daily_earnings: int = Field(..., gt=0)
    days_worked_per_month: int = Field(..., ge=1, le=30)
    work_consistency: str  # regular, irregular, seasonal
    primary_employer: Optional[str] = None
    has_bank_account: bool = False
    upi_transaction_history_consent: bool = False


class StepThreeGigWorkerData(BaseModel):
    """Step 3: Gig worker-specific data"""
    platforms: List[str]  # Ola, Zomato, Uber, etc.
    platform_registration_ids: Dict[str, str]
    average_weekly_earnings: int = Field(..., gt=0)
    active_days_per_week: float = Field(..., gt=0, le=7)
    months_on_platform: int = Field(..., gt=0)
    platform_count: int = Field(..., ge=1)


class StepThreeMSMEData(BaseModel):
    """Step 3: MSME owner-specific data"""
    business_type: str
    business_age_months: int = Field(..., gt=0)
    monthly_revenue: int = Field(..., gt=0)
    monthly_expenses: int = Field(..., ge=0)
    number_of_employees: int = Field(default=0, ge=0)
    gst_registration_number: Optional[str] = None
    udyam_registration_number: Optional[str] = None
    primary_sales_channel: str  # offline, online, both


class StepThreeHomemakerData(BaseModel):
    """Step 3: Homemaker-specific data"""
    household_monthly_income: int = Field(..., gt=0)
    spouse_employment_status: Optional[str] = None
    number_of_dependents: int = Field(..., ge=0)
    household_monthly_expenses: int = Field(..., ge=0)


class StepThreeSalariedData(BaseModel):
    """Step 3: Low-income salaried-specific data"""
    employer_name: str
    employer_type: str  # private, govt, ngo, informal
    monthly_salary_net: int = Field(..., gt=0)
    employment_tenure_months: int = Field(..., gt=0)
    salary_credited_to_bank: bool
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None


class NomineeData(BaseModel):
    """Nominee/endorser framework data"""
    full_name: str
    relationship: str  # spouse, parent, sibling, employer, community_leader
    phone_number: str
    aadhaar_number: Optional[str] = None
    employment_type: Optional[str] = None
    monthly_income: Optional[int] = None
    collateral_type: Optional[str] = None  # property, vehicle, gold, fd, livestock
    collateral_value: Optional[int] = None


class LoanApplicationSubmitRequest(BaseModel):
    """Complete loan application submission"""
    # Step 1: Personal details
    full_name: str
    date_of_birth: Union[datetime, date]
    gender: Optional[str] = None
    phone_number: str
    email: EmailStr
    aadhaar_number: Optional[str] = None
    
    # Step 2: Category
    user_category: str
    
    # Step 3: Category-specific data (flexible)
    category_data: Dict[str, Any]
    
    # Optional: Nominee
    nominee: Optional[NomineeData] = None
    
    # Loan request
    requested_amount: int = Field(..., gt=0)
    requested_tenure_months: int = Field(..., gt=0)
    loan_purpose: Optional[str] = None

    @field_validator('date_of_birth', mode='after')
    def normalize_date_of_birth(cls, value):
        if isinstance(value, date) and not isinstance(value, datetime):
            return datetime.combine(value, time.min)
        return value


class LoanApplicationResponse(BaseModel):
    """Submitted loan application response"""
    application_id: str
    application_number: str
    status: str
    created_at: datetime
    fraud_check_passed: bool
    fraud_score: Optional[float] = None
    next_step: str
    
    class Config:
        from_attributes = True


# ─── CREDIT SCORING SCHEMAS ────────────────────────────────────────────────

class CreditScoreResponse(BaseModel):
    """Credit score output"""
    credit_score: int = Field(..., ge=300, le=850)
    score_band: str
    probability_of_default: float = Field(..., ge=0, le=1)
    risk_tier: str
    
    # Loan recommendation
    eligibility: str  # APPROVED, REJECTED, HOLD
    suggested_amount: Optional[int] = None
    suggested_tenure_months: Optional[int] = None
    interest_rate_min: Optional[float] = None
    interest_rate_max: Optional[float] = None
    estimated_emi_min: Optional[int] = None
    estimated_emi_max: Optional[int] = None
    repayment_type: str = "monthly_direct_debit"
    
    # Score breakdown
    income_stability_score: int = Field(..., ge=0, le=25)
    repayment_capacity_score: int = Field(..., ge=0, le=30)
    spending_data_score: int = Field(..., ge=0, le=15)
    profile_completeness_score: int = Field(..., ge=0, le=10)
    alternative_data_score: int = Field(..., ge=0, le=20)
    
    # Top factors
    top_positive_factors: List[str]
    top_negative_factors: List[str]
    
    # SHAP explanation
    shap_summary: Optional[str] = None


class WhatIfSimulatorRequest(BaseModel):
    """What-If simulator parameters"""
    application_id: str
    
    # What-if parameters (all optional - user adjusts some)
    adjusted_income_percentage: Optional[int] = None  # ±50%
    adjusted_loan_amount: Optional[int] = None
    adjusted_tenure_months: Optional[int] = None
    add_nominee: Optional[bool] = None
    add_collateral: Optional[Dict[str, Any]] = None


class WhatIfSimulatorResponse(BaseModel):
    """What-If simulator results"""
    adjusted_credit_score: int
    adjusted_probability_of_default: float
    adjusted_eligibility: str
    adjusted_approved_amount: Optional[int] = None
    adjusted_interest_rate_min: Optional[float] = None
    adjusted_interest_rate_max: Optional[float] = None
    adjusted_emi: Optional[int] = None
    score_change: int
    pd_change: float


# ─── CHAT SCHEMAS ──────────────────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
    """Chat message request payload."""
    message: str = Field(..., min_length=1, max_length=1000)
    application_id: Optional[str] = None


# ─── ADMIN SCHEMAS ─────────────────────────────────────────────────────────

class ApplicationListFilter(BaseModel):
    """Filter parameters for application list"""
    status: Optional[str] = None
    user_category: Optional[str] = None
    risk_band: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    application_number: Optional[str] = None
    user_id: Optional[str] = None
    fraud_score_min: Optional[float] = None
    fraud_score_max: Optional[float] = None
    loan_amount_min: Optional[int] = None
    loan_amount_max: Optional[int] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ApplicationDetailResponse(BaseModel):
    """Full application details for admin review"""
    application_id: str
    application_number: str
    user: UserResponse
    status: str
    
    # Fraud checks
    fraud_score: float
    fraud_check_details: Dict[str, Any]
    
    # ML Scoring
    credit_score: Optional[int] = None
    probability_of_default: Optional[float] = None
    risk_band: Optional[str] = None
    
    # Policy checks
    policy_checks_passed: Optional[bool] = None
    policy_check_details: Dict[str, Any]
    
    # Category data
    user_category: str
    category_data: Dict[str, Any]
    
    # Nominee
    has_nominee: bool
    nominee_data: Optional[Dict[str, Any]] = None
    
    # Loan request
    requested_amount: int
    requested_tenure_months: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DecisionRequest(BaseModel):
    """Admin decision request"""
    decision_type: str  # approved, rejected, hold, referred
    reason: str
    
    # If approved, terms
    approved_amount: Optional[int] = None
    approved_tenure_months: Optional[int] = None
    approved_interest_rate: Optional[float] = None


class DashboardKPInumerical(BaseModel):
    """Dashboard KPI response"""
    total_applications: int
    applications_today: int
    applications_this_week: int
    applications_this_month: int
    approval_rate: float
    average_credit_score: float
    average_loan_amount: int
    portfolio_at_risk_pct: float
    fraud_detection_rate: float
    average_processing_hours: float


# ─── UTILITY SCHEMAS ───────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: str
    status_code: int
    timestamp: datetime


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
