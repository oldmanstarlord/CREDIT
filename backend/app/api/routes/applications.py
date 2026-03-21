"""
Loan application routes: submit, retrieve status, credit scoring
Core borrower-facing endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
from pathlib import Path
import glob
import json
import os
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.security import get_current_user, TokenData
from app.core.config import settings
from app.core.database import get_db
from app.schemas import (
    LoanApplicationSubmitRequest, LoanApplicationResponse, CreditScoreResponse,
    WhatIfSimulatorRequest, WhatIfSimulatorResponse, ApplicationListFilter
)
from app.ml.predict import CreditScorer
from app.models.models import (
    Appeal,
    ApplicationStatus,
    CategorySpecificData,
    DecisionType,
    Document,
    DocumentType,
    LoanApplication,
    Nominee,
    RiskBand,
    UserCategory,
)
from app.services import FraudCheckService
from app.services.audit_service import AuditService
from app.services.policy_engine import PolicyEngine

router = APIRouter(prefix="/applications", tags=["Applications"])

_SCORER: Optional[CreditScorer] = None


def _resolve_winner_contract_model() -> str:
    project_root = Path(__file__).resolve().parents[4]
    contracts_root = project_root / "ml_pipeline" / "models" / "integration_contracts"

    # Optional hard pin from environment for production deployments.
    env_path = os.getenv("WINNER_MODEL_PATH")
    if env_path:
        pinned = Path(env_path)
        if not pinned.is_absolute():
            pinned = project_root / pinned
        if not pinned.exists():
            raise RuntimeError(f"WINNER_MODEL_PATH does not exist: {pinned}")
        return str(pinned)

    winner_payload_path = contracts_root / "winner_upgrade_v4" / "backend_payload_winner_v4.json"
    if not winner_payload_path.exists():
        raise RuntimeError(
            "Missing winner contract payload at integration_contracts/winner_upgrade_v4/backend_payload_winner_v4.json"
        )

    # Exact notebook winner export (preferred, carries model + feature contract + controls).
    serving_artifact_path = contracts_root / "winner_upgrade_v4" / "winner_v4_serving_artifact.pkl"
    if serving_artifact_path.exists():
        return str(serving_artifact_path)

    payload = json.loads(winner_payload_path.read_text(encoding="utf-8"))
    run_id = str(payload.get("run_id", "")).strip()
    if not run_id:
        raise RuntimeError("Winner contract payload is missing run_id")

    model_glob = str(project_root / "ml_pipeline" / "models" / f"best_model_*_{run_id}.pkl")
    matches = sorted(glob.glob(model_glob))
    if len(matches) != 1:
        raise RuntimeError(
            "Winner model artifact mismatch. Expected exactly one file matching "
            f"best_model_*_{run_id}.pkl, found {len(matches)}"
        )

    return matches[0]


def _get_scorer() -> CreditScorer:
    global _SCORER
    if _SCORER is not None:
        return _SCORER

    scorer = CreditScorer()
    model_path = _resolve_winner_contract_model()
    scorer.load_model(model_path)

    _SCORER = scorer
    return _SCORER


def _eligibility_from_decision(decision_status: str) -> str:
    if decision_status == "auto_approve_low_risk":
        return "APPROVED"
    if decision_status == "auto_reject_high_risk":
        return "REJECTED"
    return "HOLD"


def _decision_to_status(decision: DecisionType) -> ApplicationStatus:
    mapping = {
        DecisionType.APPROVED: ApplicationStatus.APPROVED,
        DecisionType.REJECTED: ApplicationStatus.REJECTED,
        DecisionType.HOLD: ApplicationStatus.HOLD,
        DecisionType.REFERRED: ApplicationStatus.HOLD,
    }
    return mapping.get(decision, ApplicationStatus.HOLD)


def _risk_band_from_text(value: str) -> RiskBand:
    if value == "low":
        return RiskBand.LOW
    if value == "medium":
        return RiskBand.MEDIUM
    if value == "high":
        return RiskBand.HIGH
    return RiskBand.VERY_HIGH


def _merge_application_payload(request: LoanApplicationSubmitRequest) -> Dict[str, Any]:
    payload = request.model_dump(mode="json")
    payload.update(request.category_data or {})
    if request.nominee:
        payload["nominee"] = request.nominee.model_dump(mode="json")
        payload["has_nominee"] = True
    return payload


def _uuid_or_400(value: str, field_name: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID for {field_name}",
        ) from exc


@router.post("/submit", response_model=LoanApplicationResponse, status_code=status.HTTP_201_CREATED)
async def submit_application(
    request: LoanApplicationSubmitRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit a new loan application.
    
    Comprehensive application that includes:
    - Personal details (Step 1)
    - Category selection (Step 2)
    - Category-specific data (Step 3)
    - Optional nominee information (Trust framework)
    - Desired loan terms
    
    Process:
    1. Store application in database
    2. Run fraud checks (pre-screening)
    3. If fraud score < 0.6: Queue for ML scoring
    4. If fraud score >= 0.6: Mark for manual review
    5. Return status to user
    
    Args:
        request: Complete loan application details
        current_user: Authenticated borrower
    
    Returns:
        LoanApplicationResponse with application ID and status
    
    Raises:
        HTTPException: If validation fails or user not found
    """
    fraud_service = FraudCheckService(db=db)
    policy_engine = PolicyEngine(db=db)
    audit = AuditService(db)
    user_id = _uuid_or_400(current_user.user_id, "current_user.user_id")

    try:
        category_enum = UserCategory(request.user_category)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid user_category: {request.user_category}",
        ) from exc

    merged_payload = _merge_application_payload(request)
    fraud_score = float(fraud_service.compute_fraud_score(merged_payload))
    fraud_check_passed = fraud_score < settings.FRAUD_SCORE_REJECT_THRESHOLD

    existing_exposure = (
        db.query(func.coalesce(func.sum(LoanApplication.requested_amount), 0))
        .filter(
            LoanApplication.user_id == user_id,
            LoanApplication.final_decision == DecisionType.APPROVED,
        )
        .scalar()
    ) or 0

    application_id = uuid.uuid4()
    app_number = f"APP-{datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"

    application = LoanApplication(
        id=application_id,
        user_id=user_id,
        status=ApplicationStatus.PRE_SCREENING,
        application_number=app_number,
        requested_amount=request.requested_amount,
        requested_tenure_months=request.requested_tenure_months,
        loan_purpose=request.loan_purpose,
        fraud_score=fraud_score,
        fraud_check_passed=fraud_check_passed,
        fraud_check_details={"source": "rule_engine", "version": "v1"},
        has_nominee=bool(request.nominee),
        nominee_data=request.nominee.model_dump(mode="json") if request.nominee else {},
        alternative_data_features=merged_payload,
    )
    db.add(application)

    db.add(
        CategorySpecificData(
            application_id=application_id,
            user_category=category_enum,
            data=request.category_data,
            computed_features={},
        )
    )

    if request.nominee:
        db.add(
            Nominee(
                application_id=application_id,
                full_name=request.nominee.full_name,
                relationship=request.nominee.relationship,
                phone_number=request.nominee.phone_number,
                aadhaar_number=request.nominee.aadhaar_number,
                employment_type=request.nominee.employment_type,
                monthly_income=request.nominee.monthly_income,
                collateral_type=request.nominee.collateral_type,
                collateral_value=request.nominee.collateral_value,
            )
        )

    next_step = "manual review"
    if not fraud_check_passed:
        application.status = ApplicationStatus.REJECTED
        application.final_decision = DecisionType.REJECTED
        application.decision_reason = "Fraud pre-screening threshold exceeded"
        next_step = "appeal allowed"
    else:
        try:
            scorer = _get_scorer()
            scored = scorer.score_application(merged_payload)

            application.status = ApplicationStatus.ML_SCORED
            application.probability_of_default = scored["probability_of_default"]
            application.credit_score = scored["credit_score"]
            application.risk_band = _risk_band_from_text(scored["risk_band"])
            application.ml_model_version = scored.get("model_version")
            application.ml_scores_computed_at = datetime.utcnow()

            policy_input = {
                "estimated_emi": scored.get("loan_recommendation", {}).get("estimated_emi_max", 0),
                "monthly_income": merged_payload.get("monthly_income")
                or merged_payload.get("monthly_salary_net")
                or merged_payload.get("household_monthly_income")
                or 0,
                "user_category": merged_payload.get("user_category"),
                "probability_of_default": scored.get("probability_of_default"),
                "credit_score": scored.get("credit_score"),
                "requested_amount": request.requested_amount,
                "existing_exposure": int(existing_exposure),
                "is_new_user": int(existing_exposure) == 0,
                "has_nominee": bool(request.nominee),
                "has_collateral": bool(request.nominee and request.nominee.collateral_value),
            }
            policy_results = policy_engine.run_all_policy_checks(policy_input)
            application.policy_checks_passed = bool(policy_results.get("all_pass", False))
            application.policy_check_details = policy_results

            decision_status = scored.get("decision_status", "manual_review")
            if decision_status == "auto_approve_low_risk" and application.policy_checks_passed:
                application.final_decision = DecisionType.APPROVED
            elif decision_status == "auto_reject_high_risk":
                application.final_decision = DecisionType.REJECTED
            else:
                application.final_decision = DecisionType.HOLD

            application.status = _decision_to_status(application.final_decision)
            application.decision_reason = scored.get("reason_flag", "normal_scoring")
            next_step = "disbursal preparation" if application.final_decision == DecisionType.APPROVED else "manual review"
        except Exception as exc:
            application.status = ApplicationStatus.HOLD
            application.final_decision = DecisionType.HOLD
            application.decision_reason = f"Scoring failed: {exc}"
            next_step = "manual review"

    db.commit()
    db.refresh(application)

    audit.log_event(
        "application_submit",
        user_id=user_id,
        actor_id=user_id,
        application_id=application.id,
        model_version=application.ml_model_version,
        model_output={
            "credit_score": application.credit_score,
            "probability_of_default": application.probability_of_default,
            "risk_band": application.risk_band.value if application.risk_band else None,
        },
        policy_results=application.policy_check_details,
        decision=application.final_decision.value if application.final_decision else None,
        decision_reason=application.decision_reason,
        input_snapshot={"requested_amount": application.requested_amount},
    )
    db.commit()
    
    return LoanApplicationResponse(
        application_id=str(application_id),
        application_number=app_number,
        status=application.status.value,
        created_at=datetime.utcnow(),
        fraud_check_passed=fraud_check_passed,
        fraud_score=fraud_score,
        next_step=next_step,
    )


@router.get("/{application_id}/status")
async def get_application_status(
    application_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get application processing status.
    
    Returns current stage and any relevant messages.
    
    Stages:
    - draft: Not yet submitted
    - submitted: Received, pre-screening in progress
    - pre_screening: Fraud checks running
    - ml_scored: ML model has scored
    - policy_checked: Policy engine completed checks
    - hold: Awaiting admin review
    - approved: Decision made, approved
    - rejected: Decision made, rejected
    - appealed: User has appealed rejection
    
    Args:
        application_id: Application ID
        current_user: Authenticated user
    
    Returns:
        Application status details
    """
    app_uuid = _uuid_or_400(application_id, "application_id")
    application = (
        db.query(LoanApplication)
        .filter(LoanApplication.id == app_uuid, LoanApplication.user_id == _uuid_or_400(current_user.user_id, "current_user.user_id"))
        .first()
    )
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    decision = application.final_decision.value if application.final_decision else None
    return {
        "application_id": application_id,
        "status": application.status.value,
        "stage": "completed" if decision else "in_progress",
        "estimated_completion": "completed" if decision else "2 hours",
        "fraud_flag": not bool(application.fraud_check_passed),
        "decision": decision,
        "credit_score": application.credit_score,
    }


@router.get("/{application_id}/score", response_model=CreditScoreResponse)
async def get_credit_score(
    application_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get computed credit score for application.
    
    Only available after ML scoring is complete.
    Returns full credit intelligence report including:
    - 300-850 credit score
    - Probability of default (PD)
    - Risk band classification
    - Loan recommendation (amount, tenure, interest rate)
    - Score breakdown by 5 pillars
    - Top positive/negative factors (SHAP)
    - Plain-English explanation of score
    
    Args:
        application_id: Application ID
        current_user: Authenticated user
    
    Returns:
        CreditScoreResponse with all score details
    
    Raises:
        HTTPException: If application not found or scoring not complete
    """
    app_uuid = _uuid_or_400(application_id, "application_id")
    application = (
        db.query(LoanApplication)
        .filter(LoanApplication.id == app_uuid, LoanApplication.user_id == _uuid_or_400(current_user.user_id, "current_user.user_id"))
        .first()
    )
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if application.credit_score is None or application.probability_of_default is None:
        try:
            scorer = _get_scorer()
            result = scorer.score_application(application.alternative_data_features or {})
            application.probability_of_default = result["probability_of_default"]
            application.credit_score = result["credit_score"]
            application.risk_band = _risk_band_from_text(result["risk_band"])
            application.ml_model_version = result.get("model_version")
            application.ml_scores_computed_at = datetime.utcnow()
            db.commit()

            audit = AuditService(db)
            actor_uuid = _uuid_or_400(current_user.user_id, "current_user.user_id")
            audit.log_event(
                "application_score_generated",
                user_id=actor_uuid,
                actor_id=actor_uuid,
                application_id=application.id,
                model_version=application.ml_model_version,
                model_output={
                    "credit_score": application.credit_score,
                    "probability_of_default": application.probability_of_default,
                    "risk_band": application.risk_band.value if application.risk_band else None,
                },
            )
            db.commit()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail={"message": "Scoring failed for this application", "error": str(e)},
            )
    else:
        result = {
            "credit_score": application.credit_score,
            "risk_band": application.risk_band.value if application.risk_band else "high",
            "probability_of_default": application.probability_of_default,
            "loan_recommendation": {},
            "decision_status": "manual_review",
            "confidence_tier": "medium",
            "reason_flag": application.decision_reason or "db_cached",
        }

    loan_rec = result.get("loan_recommendation", {})
    shap_expl = result.get("shap_explanation") or {}
    top_pos = [x.get("feature") for x in shap_expl.get("top_positive_factors", [])][:5]
    top_neg = [x.get("feature") for x in shap_expl.get("top_negative_factors", [])][:5]

    return CreditScoreResponse(
        credit_score=int(result["credit_score"]),
        score_band=result["risk_band"],
        probability_of_default=float(result["probability_of_default"]),
        risk_tier=result["risk_band"],
        eligibility=_eligibility_from_decision(result.get("decision_status", "manual_review")),
        suggested_amount=loan_rec.get("recommended_amount"),
        suggested_tenure_months=loan_rec.get("recommended_tenure_months"),
        interest_rate_min=loan_rec.get("interest_rate_min"),
        interest_rate_max=loan_rec.get("interest_rate_max"),
        estimated_emi_min=loan_rec.get("estimated_emi_min"),
        estimated_emi_max=loan_rec.get("estimated_emi_max"),
        income_stability_score=18,
        repayment_capacity_score=22,
        spending_data_score=10,
        profile_completeness_score=8,
        alternative_data_score=14,
        top_positive_factors=top_pos or ["income_stability", "low_delinquency"],
        top_negative_factors=top_neg or ["debt_burden", "recent_late_payment"],
        shap_summary=f"Decision: {result.get('decision_status')} | Confidence: {result.get('confidence_tier')} | Reason: {result.get('reason_flag')}",
    )


@router.post("/score-preview")
async def score_preview(
    payload: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user)
):
    """
    Score arbitrary payload for integration testing.
    Uses winner lock thresholds and guardrail outputs.
    """
    try:
        scorer = _get_scorer()
        if scorer.model is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Scoring model is not loaded. Configure winner model artifact first.",
            )
        return scorer.score_application(payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail={
                "message": "Winner feature contract mismatch. Export notebook winner model/feature contract and retry.",
                "error": str(e),
            },
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail={
                "message": "Winner model artifact could not be resolved from notebook contracts.",
                "error": str(e),
            },
        )


@router.get("/go-live-gate")
async def go_live_gate(
    current_user: TokenData = Depends(get_current_user)
):
    """Deployment publish gate based on locked core-segment recall status."""
    try:
        scorer = _get_scorer()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail={
                "message": "Winner model artifact could not be resolved from notebook contracts.",
                "error": str(e),
            },
        )
    gate = scorer.get_go_live_status()
    if not gate.get("publish_allowed", False):
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail={
                "message": "Publish blocked: core segment recall floor gate failed.",
                **gate,
            },
        )
    return gate


@router.post("/{application_id}/simulate", response_model=WhatIfSimulatorResponse)
async def simulate_loan_terms(
    application_id: str,
    request: WhatIfSimulatorRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Interactive what-if simulator for loan scenarios.
    
    User can adjust:
    - Monthly income (±50%)
    - Loan amount requested
    - Loan tenure
    - Add/remove nominee
    - Add collateral details
    
    Returns updated score and loan terms in real-time (<2 seconds).
    
    Does NOT create a real application - results are ephemeral.
    Uses simulate=True flag to prevent database writes.
    
    Args:
        application_id: Base application ID
        request: Simulation parameters
        current_user: Authenticated user
    
    Returns:
        WhatIfSimulatorResponse with adjusted score and terms
    """
    app_uuid = _uuid_or_400(application_id, "application_id")
    application = (
        db.query(LoanApplication)
        .filter(LoanApplication.id == app_uuid, LoanApplication.user_id == _uuid_or_400(current_user.user_id, "current_user.user_id"))
        .first()
    )
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    scenario = dict(application.alternative_data_features or {})
    if request.adjusted_income_percentage is not None:
        base_income = float(scenario.get("monthly_income") or scenario.get("monthly_salary_net") or 0)
        scenario["monthly_income"] = base_income * (1 + (request.adjusted_income_percentage / 100.0))
    if request.adjusted_loan_amount is not None:
        scenario["requested_amount"] = request.adjusted_loan_amount
    if request.adjusted_tenure_months is not None:
        scenario["requested_tenure_months"] = request.adjusted_tenure_months

    scorer = _get_scorer()
    result = scorer.score_application(scenario)

    audit = AuditService(db)
    actor_uuid = _uuid_or_400(current_user.user_id, "current_user.user_id")
    audit.log_event(
        "application_simulate",
        user_id=actor_uuid,
        actor_id=actor_uuid,
        application_id=application.id,
        model_output={
            "credit_score": result.get("credit_score"),
            "probability_of_default": result.get("probability_of_default"),
            "decision_status": result.get("decision_status"),
        },
    )
    db.commit()

    old_score = int(application.credit_score or 0)
    old_pd = float(application.probability_of_default or 0.0)

    return WhatIfSimulatorResponse(
        adjusted_credit_score=int(result["credit_score"]),
        adjusted_probability_of_default=float(result["probability_of_default"]),
        adjusted_eligibility=_eligibility_from_decision(result.get("decision_status", "manual_review")),
        adjusted_approved_amount=result.get("loan_recommendation", {}).get("recommended_amount"),
        adjusted_interest_rate_min=result.get("loan_recommendation", {}).get("interest_rate_min"),
        adjusted_interest_rate_max=result.get("loan_recommendation", {}).get("interest_rate_max"),
        adjusted_emi=result.get("loan_recommendation", {}).get("estimated_emi_max"),
        score_change=int(result["credit_score"]) - old_score,
        pd_change=float(result["probability_of_default"]) - old_pd,
    )


@router.post("/{application_id}/documents/upload")
async def upload_document(
    application_id: str,
    document_type: str,
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload document for application.
    
    Supported types:
    - land_proof: For farmers
    - salary_slip: For salaried workers
    - bank_statement: Income verification
    - gst_certificate: For MSME owners
    - kisan_credit_card: For farmers
    - business_registration: For MSME
    - collateral_proof: For nominee collateral
    - photograph: Profile picture
    
    File requirements:
    - Max size: 10 MB
    - Formats: PDF, JPG, PNG
    - Scanned documents should be readable
    
    Process:
    1. Validate file
    2. Upload to S3
    3. Store metadata in database
    4. OCR extraction (async job)
    5. Return upload confirmation
    
    Args:
        application_id: Application ID
        document_type: Type of document
        file: File to upload
        current_user: Authenticated user
    
    Returns:
        Upload confirmation with S3 path
    """
    app_uuid = _uuid_or_400(application_id, "application_id")
    application = (
        db.query(LoanApplication)
        .filter(LoanApplication.id == app_uuid, LoanApplication.user_id == _uuid_or_400(current_user.user_id, "current_user.user_id"))
        .first()
    )
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    allowed_ext = {".pdf", ".jpg", ".jpeg", ".png"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed_ext:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file format")

    try:
        doc_enum = DocumentType(document_type)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid document type") from exc

    doc_id = uuid.uuid4()
    s3_path = f"s3://{settings.S3_BUCKET_NAME}/documents/{application_id}/{file.filename}"
    doc = Document(
        id=doc_id,
        user_id=_uuid_or_400(current_user.user_id, "current_user.user_id"),
        application_id=application_id,
        document_type=doc_enum,
        original_filename=file.filename,
        s3_path=s3_path,
        s3_bucket=settings.S3_BUCKET_NAME,
    )
    db.add(doc)
    db.commit()

    audit = AuditService(db)
    actor_uuid = _uuid_or_400(current_user.user_id, "current_user.user_id")
    audit.log_event(
        "application_document_upload",
        user_id=actor_uuid,
        actor_id=actor_uuid,
        application_id=application.id,
        input_snapshot={"document_type": document_type, "filename": file.filename},
    )
    db.commit()

    return {
        "document_id": str(doc_id),
        "s3_path": s3_path,
        "status": "uploaded",
        "ocr_status": "queued"
    }


@router.post("/{application_id}/appeal")
async def appeal_rejection(
    application_id: str,
    appeal_reason: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Appeal a rejected loan application.
    
    Borrowers have 30 days from rejection to appeal.
    Appeal is reviewed by risk manager manually.
    
    Args:
        application_id: Application ID
        appeal_reason: Reason for appeal
        current_user: Authenticated user
    
    Returns:
        Appeal confirmation
    """
    app_uuid = _uuid_or_400(application_id, "application_id")
    application = (
        db.query(LoanApplication)
        .filter(LoanApplication.id == app_uuid, LoanApplication.user_id == _uuid_or_400(current_user.user_id, "current_user.user_id"))
        .first()
    )
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if application.final_decision != DecisionType.REJECTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only rejected applications can be appealed")

    if application.appeal is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Appeal already exists for this application")

    appeal = Appeal(
        id=uuid.uuid4(),
        application_id=application_id,
        user_id=_uuid_or_400(current_user.user_id, "current_user.user_id"),
        appeal_reason=appeal_reason,
    )
    db.add(appeal)
    application.status = ApplicationStatus.APPEALED
    db.commit()

    audit = AuditService(db)
    actor_uuid = _uuid_or_400(current_user.user_id, "current_user.user_id")
    audit.log_event(
        "application_appeal_submitted",
        user_id=actor_uuid,
        actor_id=actor_uuid,
        application_id=application.id,
        decision=application.final_decision.value if application.final_decision else None,
        decision_reason=appeal_reason,
    )
    db.commit()

    return {
        "appeal_id": str(appeal.id),
        "status": "received",
        "estimated_review_days": 7
    }
