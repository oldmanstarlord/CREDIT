"""
Configuration management for Barclays Credit Platform
Loads settings from environment variables with sensible defaults
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Barclays Credit Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    DOCS_URL: str = "/docs"
    OPENAPI_URL: str = "/openapi.json"
    
    # Database
    DATABASE_URL: str = "postgresql://admin:postgres@localhost:5432/barclays_credit"
    SQLALCHEMY_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_CACHE_EXPIRY: int = 3600  # 1 hour
    
    # JWT / Security
    JWT_SECRET: str = "change-me-in-env"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # AWS
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "barclays-credit-platform"
    S3_LOGS_BUCKET: str = "barclays-credit-platform-logs"
    
    # LLM / GenAI
    LLM_PROVIDER: str = "openrouter"  # openrouter | openai

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_BASE_URL: Optional[str] = None

    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "meta-llama/llama-3.1-8b-instruct:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_SITE_URL: Optional[str] = None
    OPENROUTER_APP_NAME: str = "Barclays Credit Intelligence Platform"

    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 500
    
    # ML Model Configuration
    ML_MODEL_VERSION: str = "v1.0.0"
    DECISION_THRESHOLD: float = 0.35
    AUTO_REJECT_PD_THRESHOLD: float = 0.65
    AUTO_APPROVE_PD_THRESHOLD: float = 0.15
    MIN_CREDIT_SCORE_FOR_APPROVAL: int = 500
    
    # Business Rules
    EMI_TO_INCOME_MAX_RATIO: float = 0.40
    FARMER_EMI_TO_INCOME_MAX: float = 0.30
    DAILY_WORKER_EMI_TO_INCOME_MAX: float = 0.25
    MAX_LOAN_WITHOUT_COLLATERAL: int = 100000  # ₹1,00,000
    MAX_EXPOSURE_PER_USER: int = 1000000  # ₹10,00,000
    NEW_USER_MAX_LOAN: int = 50000  # ₹50,000
    
    # Fraud Detection
    FRAUD_SCORE_HOLD_THRESHOLD: float = 0.3
    FRAUD_SCORE_REJECT_THRESHOLD: float = 0.6
    
    # Feature Flags
    ENABLE_S3_UPLOAD: bool = True
    ENABLE_GENAI_EXPLANATIONS: bool = True
    ENABLE_FAIRNESS_MONITORING: bool = True
    SIMULATE_MODE: bool = False  # for testing without real ML
    
    # Email Configuration (for notifications)
    EMAIL_BACKEND: str = "smtp"
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@barclays-credit.com"

    # Dataset Paths (workspace-level)
    DATASETS_ROOT: str = "../datasets"
    DATASETS_RAW_DIR: str = "../datasets/raw"
    DATASETS_ARCHIVES_DIR: str = "../datasets/archives"

    MYTRANSACTION_CSV: str = "../datasets/raw/my-transaction/MyTransaction.csv"
    PAYSIM_FRAUD_CSV: str = "../datasets/raw/paysim-fraud/PS_20174392719_1491204439457_log.csv"
    GMSC_TRAIN_CSV: str = "../datasets/raw/give-me-some-credit/cs-training.csv"
    GMSC_TEST_CSV: str = "../datasets/raw/give-me-some-credit/cs-test.csv"
    GMSC_SAMPLE_SUBMISSION_CSV: str = "../datasets/raw/give-me-some-credit/sampleEntry.csv"
    HOME_CREDIT_TRAIN_CSV: str = "../datasets/raw/home-credit/application_train.csv"
    HOME_CREDIT_TEST_CSV: str = "../datasets/raw/home-credit/application_test.csv"
    HOME_CREDIT_COLUMNS_DESCRIPTION_CSV: str = "../datasets/raw/home-credit/HomeCredit_columns_description.csv"
    LENDING_CLUB_LOAN_CSV: str = "../datasets/raw/lending-club/loan.csv"
    LENDING_CLUB_DICTIONARY_XLSX: str = "../datasets/raw/lending-club/LCDataDictionary.xlsx"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


# Create global settings instance
settings = Settings()

# Constants
USER_CATEGORIES = [
    "farmer",
    "daily_wage_worker",
    "gig_worker",
    "msme_owner",
    "homemaker",
    "low_income_salaried"
]

INCOME_PLAUSIBILITY_RULES = {
    "farmer": {"min": 3000, "max": 200000, "monthly": False},
    "daily_wage_worker": {"min": 200, "max": 2000, "per_day": True},
    "gig_worker": {"min": 5000, "max": 150000, "monthly": True},
    "msme_owner": {"min": 10000, "max": 2000000, "monthly": True},
    "homemaker": {"min": 0, "max": 0, "relies_on_nominee": True},
    "low_income_salaried": {"min": 8000, "max": 80000, "monthly": True}
}

PLATFORM_TRUST_SCORES = {
    "ola": 0.9, "uber": 0.9, "zomato": 0.85, "swiggy": 0.85,
    "urban_company": 0.8, "dunzo": 0.75, "rapido": 0.7,
    "unknown_platform": 0.3
}

CROP_SEASON_MAP = {
    "wheat": {"harvest_months": [3, 4], "income_multiplier": 3.5},
    "rice": {"harvest_months": [10, 11], "income_multiplier": 3.0},
    "sugarcane": {"harvest_months": [11, 12, 1], "income_multiplier": 4.0},
    "cotton": {"harvest_months": [10, 11, 12], "income_multiplier": 3.5},
    "vegetables": {"harvest_months": "continuous", "income_multiplier": 1.0}
}

RISK_BANDS = {
    "low": {"min": 750, "max": 850, "label": "Low Risk"},
    "medium": {"min": 650, "max": 749, "label": "Medium Risk"},
    "high": {"min": 550, "max": 649, "label": "High Risk"},
    "very_high": {"min": 300, "max": 549, "label": "Very High Risk"}
}

SCORE_WEIGHTS = {
    "income_stability": 0.25,
    "repayment_capacity": 0.30,
    "spending_data": 0.15,
    "profile_completeness": 0.10,
    "alternative_data": 0.20
}

INTEREST_RATE_MATRIX = {
    "small_loans_up_to_1_lakh": (18, 25),
    "medium_loans_1_to_3_lakh": (12, 18),
    "large_loans_3_to_10_lakh": (10, 12),
    "premium_above_10_lakh": (8, 10)
}

CREDIT_LADDER = {
    "tier_0_new": {
        "label": "New User",
        "duration": "0–6 months since first loan",
        "eligible_products": ["micro_personal_loan"],
        "max_amount": 50000,
        "collateral_required": False,
        "interest_range": (18, 25),
    },
    "tier_1_trust_building": {
        "label": "Trust Building",
        "duration": "6–18 months with clean repayment",
        "eligible_products": ["personal_loan", "small_business_loan"],
        "max_amount": 500000,
        "interest_range": (12, 18),
    },
    "tier_2_established": {
        "label": "Established Borrower",
        "duration": "18–36 months",
        "eligible_products": ["large_personal_loan", "small_vehicle_loan"],
        "max_amount": 1000000,
        "interest_range": (10, 14)
    },
    "tier_3_prime": {
        "label": "Prime Borrower",
        "duration": "After 2–3 years",
        "min_credit_score": 650,
        "eligible_products": ["home_loan", "business_loan", "secured_loan"],
        "max_amount": None,
        "interest_range": (8, 10),
    }
}

ADMIN_ROLES = {
    "analyst": {
        "permissions": ["view_applications", "add_notes", "view_scores", "view_shap"],
        "cannot": ["approve", "reject", "override_model", "change_policy"]
    },
    "senior_analyst": {
        "permissions": ["view_applications", "add_notes", "view_scores", "view_shap", 
                       "recommend_decision", "request_override"],
        "cannot": ["final_approve", "change_policy"]
    },
    "risk_manager": {
        "permissions": ["all_analyst_permissions", "approve", "reject", "override_with_reason"],
        "override_requires": "written_justification_mandatory"
    },
    "admin": {
        "permissions": ["all_permissions", "configure_policy", "view_audit_logs", 
                       "manage_users", "model_management"]
    }
}

ENDORSER_ELIGIBILITY = {
    "min_age": 21,
    "max_existing_endorsements": 2,
    "min_income_to_loan_ratio": 3.0,
    "valid_relationships": ["spouse", "parent", "sibling", "employer", "registered_microfinance_agent"],
    "collateral_discount_factors": {
        "property": 0.70,
        "vehicle": 0.50,
        "gold": 0.85,
        "fixed_deposit": 0.90,
        "livestock": 0.40
    }
}

LATE_PAYMENT_POLICY = {
    "day_1_to_7": {"action": "reminder_sms_email", "score_impact": 0},
    "day_7_to_15": {"action": "penalty_charge", "score_impact": 0},
    "day_15_to_30": {"action": "score_drop", "score_impact_min": -20, "score_impact_max": -50},
    "day_30_plus": {"action": "defaulter_flag", "score_impact": -100, "new_loans": False}
}
