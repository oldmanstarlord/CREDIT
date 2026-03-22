"""
Database models for Barclays Credit Intelligence Platform
Comprehensive schema for user, application, scoring, and audit management
"""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text, JSON,
    ForeignKey, Enum, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship as orm_relationship
from datetime import datetime
import uuid
import enum
from app.models import Base


# ─── ENUMS ────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    """User role enumeration"""
    BORROWER = "borrower"
    ANALYST = "analyst"
    SENIOR_ANALYST = "senior_analyst"
    RISK_MANAGER = "risk_manager"
    ADMIN = "admin"


class UserCategory(str, enum.Enum):
    """Borrower category enumeration"""
    FARMER = "farmer"
    DAILY_WAGE_WORKER = "daily_wage_worker"
    GIG_WORKER = "gig_worker"
    MSME_OWNER = "msme_owner"
    HOMEMAKER = "homemaker"
    LOW_INCOME_SALARIED = "low_income_salaried"


class ApplicationStatus(str, enum.Enum):
    """Application processing status"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PRE_SCREENING = "pre_screening"
    ML_SCORED = "ml_scored"
    POLICY_CHECKED = "policy_checked"
    HOLD = "hold"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPEALED = "appealed"


class DecisionType(str, enum.Enum):
    """Decision types"""
    APPROVED = "approved"
    REJECTED = "rejected"
    HOLD = "hold"
    REFERRED = "referred"


class DocumentType(str, enum.Enum):
    """Document types"""
    LAND_PROOF = "land_proof"
    SALARY_SLIP = "salary_slip"
    BANK_STATEMENT = "bank_statement"
    AADHAR = "aadhar"
    PAN = "pan"
    GST_CERTIFICATE = "gst_certificate"
    KISAN_CREDIT_CARD = "kisan_credit_card"
    BUSINESS_REGISTRATION = "business_registration"
    COLLATERAL_PROOF = "collateral_proof"
    PHOTOGRAPH = "photograph"
    OTHER = "other"


class RiskBand(str, enum.Enum):
    """Risk band classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


# ─── USER MODELS ───────────────────────────────────────────────────────────

class User(Base):
    """
    User account model.
    Can be a borrower (applying for loans) or an admin (reviewing applications).
    """
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint('email', name='uq_email'),
        UniqueConstraint('phone_number', name='uq_phone_number'),
        UniqueConstraint('aadhaar_number', name='uq_aadhaar'),
        Index('idx_users_created_at', 'created_at'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Personal details
    email = Column(String(255), nullable=False, unique=True)
    phone_number = Column(String(20), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(10), nullable=True)  # NOT used in scoring
    aadhaar_number = Column(String(12), nullable=True, unique=True)
    aadhaar_verified = Column(Boolean, default=False)
    
    # Role and status
    role = Column(Enum(UserRole), default=UserRole.BORROWER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Borrower-specific
    user_category = Column(Enum(UserCategory), nullable=True)
    status = Column(String(50), default="active")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    applications = orm_relationship(
        "LoanApplication",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="LoanApplication.user_id",
    )
    documents = orm_relationship("Document", back_populates="user", cascade="all, delete-orphan")
    audit_logs = orm_relationship("AuditLog", back_populates="user", foreign_keys="AuditLog.user_id")


class AdminUser(Base):
    """
    Specialized user model for Barclays analysts and risk managers.
    Tracks additional permissions and activity.
    """
    __tablename__ = "admin_users"
    __table_args__ = (
        Index('idx_admin_users_user_id', 'user_id'),
        Index('idx_admin_users_role', 'role'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    role = Column(Enum(UserRole), nullable=False)
    department = Column(String(100), nullable=True)
    manager_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Permissions (JSON for flexibility)
    custom_permissions = Column(JSONB, default={})
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─── APPLICATION MODELS ────────────────────────────────────────────────────

class LoanApplication(Base):
    """
    Core loan application model.
    Tracks the complete lifecycle of a credit application.
    """
    __tablename__ = "loan_applications"
    __table_args__ = (
        Index('idx_loan_applications_user_id', 'user_id'),
        Index('idx_loan_applications_status', 'status'),
        Index('idx_loan_applications_created_at', 'created_at'),
        Index('idx_loan_applications_fraud_score', 'fraud_score'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Application metadata
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.DRAFT, nullable=False)
    application_number = Column(String(50), unique=True, nullable=False)
    
    # Applied loan details
    requested_amount = Column(Integer, nullable=False)  # in currency units (₹)
    requested_tenure_months = Column(Integer, nullable=False)
    loan_purpose = Column(String(255), nullable=True)
    
    # Pre-screening results
    fraud_score = Column(Float, nullable=True)  # 0.0 - 1.0
    fraud_check_passed = Column(Boolean, default=True)
    fraud_check_details = Column(JSONB, default={})
    
    # ML Scoring results
    probability_of_default = Column(Float, nullable=True)  # 0.0 - 1.0
    credit_score = Column(Integer, nullable=True)  # 300 - 850
    risk_band = Column(Enum(RiskBand), nullable=True)
    ml_scoring_result = Column(JSONB, default={})  # Full scorer output cached
    ml_model_version = Column(String(50), nullable=True)
    ml_scores_computed_at = Column(DateTime, nullable=True)
    
    # Policy engine checks
    policy_checks_passed = Column(Boolean, nullable=True)
    policy_check_details = Column(JSONB, default={})
    
    # Final decision
    final_decision = Column(Enum(DecisionType), nullable=True)
    decision_date = Column(DateTime, nullable=True)
    decision_reason = Column(Text, nullable=True)
    decided_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Override tracking
    decision_overridden = Column(Boolean, default=False)
    override_reason = Column(Text, nullable=True)
    override_by = Column(UUID(as_uuid=True), nullable=True)
    override_at = Column(DateTime, nullable=True)
    
    # Alternative data features (stored for audit/transparency)
    alternative_data_features = Column(JSONB, default={})
    
    # Nominee/Trust framework
    has_nominee = Column(Boolean, default=False)
    nominee_data = Column(JSONB, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = orm_relationship("User", back_populates="applications", foreign_keys=[user_id])
    category_specific_data = orm_relationship("CategorySpecificData", back_populates="application", 
                                         cascade="all, delete-orphan", uselist=False)
    nominee = orm_relationship("Nominee", back_populates="application", cascade="all, delete-orphan", 
                          uselist=False)
    documents = orm_relationship("Document", back_populates="application", cascade="all, delete-orphan")
    decisions = orm_relationship("Decision", back_populates="application", cascade="all, delete-orphan")
    shap_explanation = orm_relationship("SHAPExplanation", back_populates="application", 
                                   cascade="all, delete-orphan", uselist=False)
    appeal = orm_relationship("Appeal", back_populates="application", cascade="all, delete-orphan", uselist=False)
    chat_messages = orm_relationship("ChatHistory", back_populates="application", cascade="all, delete-orphan")


class CategorySpecificData(Base):
    """
    Flexible model for category-specific application data.
    Stores all the category-specific fields collected during onboarding.
    """
    __tablename__ = "category_specific_data"
    __table_args__ = (
        Index('idx_category_specific_data_application_id', 'application_id'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey('loan_applications.id'), nullable=False)
    
    user_category = Column(Enum(UserCategory), nullable=False)
    
    # Generic JSON field for all category-specific data
    # This allows flexibility while maintaining a relational structure
    data = Column(JSONB, nullable=False)  # Contains all category-specific fields
    
    # Precomputed features for quick access
    computed_features = Column(JSONB, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    application = orm_relationship("LoanApplication", back_populates="category_specific_data")


class Nominee(Base):
    """
    Nominee/endorser information for trust framework.
    Links to the loan application.
    """
    __tablename__ = "nominees"
    __table_args__ = (
        Index('idx_nominees_application_id', 'application_id'),
        UniqueConstraint('application_id', name='uq_application_nominee'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey('loan_applications.id'), nullable=False)
    
    # Nominee details
    full_name = Column(String(255), nullable=False)
    relationship = Column(String(50), nullable=False)  # spouse, parent, employer, etc.
    phone_number = Column(String(20), nullable=False)
    aadhaar_number = Column(String(12), nullable=True)
    
    # Eligibility
    age = Column(Integer, nullable=True)
    employment_type = Column(String(100), nullable=True)
    monthly_income = Column(Integer, nullable=True)
    
    # Collateral
    collateral_type = Column(String(100), nullable=True)  # property, vehicle, gold, etc.
    collateral_value = Column(Integer, nullable=True)
    collateral_verified = Column(Boolean, default=False)
    
    # Verification
    verified = Column(Boolean, default=False)
    verification_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    application = orm_relationship("LoanApplication", back_populates="nominee")


class Document(Base):
    """
    Document storage metadata.
    References files stored in S3.
    """
    __tablename__ = "documents"
    __table_args__ = (
        Index('idx_documents_user_id', 'user_id'),
        Index('idx_documents_application_id', 'application_id'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    application_id = Column(UUID(as_uuid=True), ForeignKey('loan_applications.id'), nullable=True)
    
    document_type = Column(Enum(DocumentType), nullable=False)
    original_filename = Column(String(255), nullable=False)
    s3_path = Column(String(500), nullable=False)
    s3_bucket = Column(String(100), nullable=False)
    
    file_size_bytes = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA-256 for integrity
    
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    verified = Column(Boolean, default=False)
    verification_notes = Column(Text, nullable=True)
    
    # Relationships
    user = orm_relationship("User", back_populates="documents")
    application = orm_relationship("LoanApplication", back_populates="documents")


# ─── DECISION AND SCORING MODELS ───────────────────────────────────────────

class Decision(Base):
    """
    Credit decision record.
    Stores the final decision and reasoning for an application.
    """
    __tablename__ = "decisions"
    __table_args__ = (
        Index('idx_decisions_application_id', 'application_id'),
        Index('idx_decisions_decision_date', 'decision_date'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey('loan_applications.id'), nullable=False)
    
    # Decision record
    decision_type = Column(Enum(DecisionType), nullable=False)  # approve, reject, hold, refer
    decision_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    decided_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Decision details
    reason = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0-1, analyst confidence
    
    # If approved, loan terms
    approved_amount = Column(Integer, nullable=True)
    approved_tenure_months = Column(Integer, nullable=True)
    approved_interest_rate = Column(Float, nullable=True)
    estimated_emi = Column(Integer, nullable=True)
    loan_tier = Column(String(50), nullable=True)  # tier_0_new, tier_1_trust_building, etc.
    
    # Override tracking
    is_override = Column(Boolean, default=False)
    override_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    application = orm_relationship("LoanApplication", back_populates="decisions")


class SHAPExplanation(Base):
    """
    SHAP explanation storage for model interpretability.
    Stores per-application feature importance explanations.
    """
    __tablename__ = "shap_explanations"
    __table_args__ = (
        Index('idx_shap_explanations_application_id', 'application_id'),
        UniqueConstraint('application_id', name='uq_application_shap'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey('loan_applications.id'), nullable=False)
    
    # SHAP values (JSON structure)
    base_value = Column(Float, nullable=False)
    shap_values = Column(JSONB, nullable=False)  # {feature_name: shap_value, ...}
    
    # Top factors
    top_positive_factors = Column(JSONB, nullable=False)  # List of (feature, value)
    top_negative_factors = Column(JSONB, nullable=False)  # List of (feature, value)
    
    # Plain English explanations (from GenAI)
    plain_english_summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    application = orm_relationship("LoanApplication", back_populates="shap_explanation")


class Appeal(Base):
    """
    Appeal record for rejected applications
    """
    __tablename__ = "appeals"
    __table_args__ = (
        Index('idx_appeals_application_id', 'application_id'),
        UniqueConstraint('application_id', name='uq_application_appeal'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey('loan_applications.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    appeal_reason = Column(Text, nullable=False)
    appeal_date = Column(DateTime, default=datetime.utcnow)
    
    # Appeal resolution
    reviewed = Column(Boolean, default=False)
    review_decision = Column(Enum(DecisionType), nullable=True)
    review_date = Column(DateTime, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    application = orm_relationship("LoanApplication", back_populates="appeal")


class ChatHistory(Base):
    """
    Persistent chat history for borrower chatbot interactions.
    """
    __tablename__ = "chat_history"
    __table_args__ = (
        Index('idx_chat_history_application_id', 'application_id'),
        Index('idx_chat_history_created_at', 'created_at'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey('loan_applications.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)

    sender = Column(String(20), nullable=False)  # user | assistant
    message = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    application = orm_relationship("LoanApplication", back_populates="chat_messages")


# ─── AUDIT AND MONITORING MODELS ───────────────────────────────────────────

class AuditLog(Base):
    """
    Immutable audit trail for all critical actions.
    Required for regulatory compliance and transparency.
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index('idx_audit_logs_user_id', 'user_id'),
        Index('idx_audit_logs_application_id', 'application_id'),
        Index('idx_audit_logs_event_timestamp', 'event_timestamp'),
        Index('idx_audit_logs_event_type', 'event_type'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identification
    event_id = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey('loan_applications.id'), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)  # applicant
    actor_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)  # who took action
    
    # Event details
    event_type = Column(String(100), nullable=False)  # submit, pre_screen, ml_score, decision, override
    event_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Snapshots for auditability
    input_snapshot = Column(JSONB, nullable=True)  # Feature values at time of scoring
    model_version = Column(String(50), nullable=True)
    model_output = Column(JSONB, nullable=True)  # PD, score, SHAP values
    policy_results = Column(JSON, nullable=True)
    
    # Decision details
    final_decision = Column(Enum(DecisionType), nullable=True)
    decision_reason = Column(Text, nullable=True)
    
    # Override tracking
    override_flag = Column(Boolean, default=False)
    override_justification = Column(Text, nullable=True)
    
    # Technical details
    ip_address = Column(String(45), nullable=True)
    session_id = Column(String(100), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Immutable - prevent modifications
    indexed = Column(Boolean, default=True)  # mark for external audit log export
    
    # Relationships
    user = orm_relationship("User", back_populates="audit_logs", foreign_keys=[user_id])


class FairnessMetric(Base):
    """
    Weekly fairness monitoring results
    """
    __tablename__ = "fairness_metrics"
    __table_args__ = (
        Index('idx_fairness_metrics_report_date', 'report_date'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    report_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Disparate impact analysis
    disparate_impact_ratios = Column(JSONB, nullable=False)  # {group_pair: ratio, ...}
    bias_detected = Column(Boolean, default=False)
    bias_severity = Column(String(50), nullable=True)  # HIGH, MEDIUM, LOW
    
    # Subgroup performance
    subgroup_performance = Column(JSONB, nullable=False)  # {group: {auc, precision, recall}, ...}
    
    # Actions taken
    action_taken = Column(Text, nullable=True)
    flagged_for_review = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelVersion(Base):
    """
    ML model registry and version tracking
    """
    __tablename__ = "model_versions"
    __table_args__ = (
        Index('idx_model_versions_version', 'version'),
        Index('idx_model_versions_deployed_at', 'deployed_at'),
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Model identification
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False, unique=True)  # v1.0.0
    
    # Training metadata
    training_date = Column(DateTime, nullable=False)
    training_datasets = Column(JSON, nullable=False)  # List of dataset names
    
    # Model performance
    auc_roc = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1_score = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=False)
    
    # Deployment
    deployed_at = Column(DateTime, nullable=True)
    deprecated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=False)
    
    # Global SHAP importance
    shap_global_importance = Column(JSONB, nullable=True)
    
    # Fairness metrics at training time
    fairness_metrics = Column(JSONB, nullable=True)
    
    # S3 location
    s3_model_path = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
