"""Admin routes aligned with core ORM schema and audit lifecycle."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import TokenData, get_current_user
from app.models.models import (
    ApplicationStatus,
    AuditLog,
    Decision,
    DecisionType,
    LoanApplication,
    User,
)
from app.services.audit_service import AuditService
from app.services.fairness_service import FairnessMonitor
from app.services.portfolio_service import MonteCarloPortfolioSimulator

import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])

REQUIRED_ROLES = {
    "get_applications": ["analyst", "senior_analyst", "risk_manager", "admin"],
    "get_application_detail": ["analyst", "senior_analyst", "risk_manager", "admin"],
    "add_notes": ["analyst", "senior_analyst", "risk_manager", "admin"],
    "make_decision": ["risk_manager", "admin"],
    "override_decision": ["risk_manager", "admin"],
    "view_audit_logs": ["risk_manager", "admin"],
}


def check_role(required_roles: List[str]):
    """Dependency checker for role-gated endpoints."""

    def role_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized for this action",
            )
        return current_user

    return role_checker


def _parse_decision(value: Optional[str]) -> Optional[DecisionType]:
    if not value:
        return None
    mapping = {
        "approved": DecisionType.APPROVED,
        "rejected": DecisionType.REJECTED,
        "hold": DecisionType.HOLD,
        "referred": DecisionType.REFERRED,
    }
    return mapping.get(value.strip().lower())


def _parse_status(value: Optional[str]) -> Optional[ApplicationStatus]:
    if not value:
        return None
    mapping = {
        "draft": ApplicationStatus.DRAFT,
        "submitted": ApplicationStatus.SUBMITTED,
        "pre_screening": ApplicationStatus.PRE_SCREENING,
        "ml_scored": ApplicationStatus.ML_SCORED,
        "policy_checked": ApplicationStatus.POLICY_CHECKED,
        "hold": ApplicationStatus.HOLD,
        "approved": ApplicationStatus.APPROVED,
        "rejected": ApplicationStatus.REJECTED,
        "appealed": ApplicationStatus.APPEALED,
    }
    return mapping.get(value.strip().lower())


def _safe_emi(principal: int, annual_rate: float, tenure_months: int) -> Optional[int]:
    if principal <= 0 or annual_rate <= 0 or tenure_months <= 0:
        return None
    monthly_rate = annual_rate / 100 / 12
    denominator = (1 + monthly_rate) ** tenure_months - 1
    if denominator == 0:
        return None
    emi = principal * monthly_rate * (1 + monthly_rate) ** tenure_months / denominator
    return int(round(emi))


@router.get("/applications", response_model=Dict[str, Any])
def get_applications(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(REQUIRED_ROLES["get_applications"])),
    stage: Optional[str] = Query(None, description="Application status/stage"),
    status_filter: Optional[str] = Query(None, description="approved|rejected|hold|referred"),
    category: Optional[str] = Query(None),
    fraud_score_min: float = Query(0.0),
    fraud_score_max: float = Query(1.0),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
):
    """Get paginated list of applications with core filters."""
    try:
        query = db.query(LoanApplication).join(User, LoanApplication.user_id == User.id)

        stage_enum = _parse_status(stage)
        if stage and not stage_enum:
            raise HTTPException(status_code=400, detail="Invalid stage filter")
        if stage_enum:
            query = query.filter(LoanApplication.status == stage_enum)

        decision_enum = _parse_decision(status_filter)
        if status_filter and not decision_enum:
            raise HTTPException(status_code=400, detail="Invalid decision filter")
        if decision_enum:
            query = query.filter(LoanApplication.final_decision == decision_enum)

        if category:
            query = query.filter(User.user_category == category)

        query = query.filter(
            and_(
                LoanApplication.fraud_score >= fraud_score_min,
                LoanApplication.fraud_score <= fraud_score_max,
            )
        )

        total_count = query.count()
        sort_columns = {
            "created_at": LoanApplication.created_at,
            "fraud_score": LoanApplication.fraud_score,
            "credit_score": LoanApplication.credit_score,
            "requested_amount": LoanApplication.requested_amount,
        }
        sort_column = sort_columns.get(sort_by, LoanApplication.created_at)
        query = query.order_by(desc(sort_column) if sort_order == "desc" else sort_column)
        applications = query.offset(offset).limit(limit).all()

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "count": len(applications),
            "applications": [
                {
                    "id": str(app.id),
                    "application_number": app.application_number,
                    "user_name": app.user.full_name if app.user else "Unknown",
                    "category": app.user.user_category.value if app.user and app.user.user_category else None,
                    "created_at": app.created_at.isoformat(),
                    "status": app.status.value if app.status else None,
                    "fraud_score": app.fraud_score,
                    "credit_score": app.credit_score,
                    "probability_of_default": app.probability_of_default,
                    "requested_amount": app.requested_amount,
                    "final_decision": app.final_decision.value if app.final_decision else None,
                }
                for app in applications
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching applications: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch applications")


@router.get("/applications/{application_id}", response_model=Dict[str, Any])
def get_application_detail(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(REQUIRED_ROLES["get_application_detail"])),
):
    """Get full application view with scoring, decision, and audit trail."""
    try:
        app_id = uuid.UUID(application_id)
        application = db.query(LoanApplication).filter(LoanApplication.id == app_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        audit_logs = (
            db.query(AuditLog)
            .filter(AuditLog.application_id == app_id)
            .order_by(desc(AuditLog.event_timestamp))
            .all()
        )

        shap = None
        if application.shap_explanation:
            shap = {
                "base_value": application.shap_explanation.base_value,
                "top_positive_factors": application.shap_explanation.top_positive_factors,
                "top_negative_factors": application.shap_explanation.top_negative_factors,
                "plain_english_summary": application.shap_explanation.plain_english_summary,
            }

        latest_decision = None
        if application.decisions:
            latest_decision = sorted(application.decisions, key=lambda d: d.decision_date or datetime.min)[-1]

        fraud_decision = "PASS"
        if application.fraud_score is not None:
            if application.fraud_score > 0.6:
                fraud_decision = "REJECT"
            elif application.fraud_score >= 0.3:
                fraud_decision = "HOLD"

        return {
            "id": str(application.id),
            "application_number": application.application_number,
            "user": {
                "id": str(application.user_id),
                "name": application.user.full_name if application.user else "",
                "email": application.user.email if application.user else "",
                "phone": application.user.phone_number if application.user else "",
            },
            "category": application.user.user_category.value if application.user and application.user.user_category else None,
            "application_data": application.category_specific_data.data if application.category_specific_data else {},
            "fraud_check": {
                "fraud_score": application.fraud_score,
                "fraud_decision": fraud_decision,
                "fraud_details": application.fraud_check_details or {},
            },
            "ml_scoring": {
                "credit_score": application.credit_score,
                "probability_of_default": application.probability_of_default,
                "risk_band": application.risk_band.value if application.risk_band else None,
                "shap_explanation": shap,
            },
            "policy_check": {
                "all_passed": application.policy_checks_passed,
                "details": application.policy_check_details or {},
            },
            "decision": {
                "final_decision": application.final_decision.value if application.final_decision else None,
                "decision_timestamp": application.decision_date.isoformat() if application.decision_date else None,
                "decision_reason": application.decision_reason,
                "override_flag": application.decision_overridden,
                "override_justification": application.override_reason,
            },
            "loan_terms": {
                "requested_amount": application.requested_amount,
                "approved_amount": latest_decision.approved_amount if latest_decision else None,
                "approved_interest_rate": latest_decision.approved_interest_rate if latest_decision else None,
                "approved_tenure_months": latest_decision.approved_tenure_months if latest_decision else None,
                "estimated_emi": latest_decision.estimated_emi if latest_decision else None,
            },
            "audit_trail": [
                {
                    "event_id": str(log.event_id),
                    "event_type": log.event_type,
                    "timestamp": log.event_timestamp.isoformat(),
                    "actor_id": str(log.actor_id) if log.actor_id else None,
                    "input_snapshot": log.input_snapshot,
                    "model_output": log.model_output,
                    "policy_results": log.policy_results,
                }
                for log in audit_logs[:20]
            ],
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching application detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch application detail")


@router.post("/applications/{application_id}/notes")
def add_notes(
    application_id: str,
    note_text: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(REQUIRED_ROLES["add_notes"])),
):
    """Store analyst note as immutable audit event."""
    try:
        app_id = uuid.UUID(application_id)
        application = db.query(LoanApplication).filter(LoanApplication.id == app_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        audit = AuditService(db)
        audit.log_event(
            "note_added",
            actor_id=uuid.UUID(current_user.user_id),
            application_id=app_id,
            input_snapshot={"note": note_text},
        )
        db.commit()
        return {"status": "success", "note_added": True}
    except ValueError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid application_id")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding notes: {e}")
        raise HTTPException(status_code=500, detail="Failed to add note")


@router.put("/applications/{application_id}/decide")
def make_decision(
    application_id: str,
    decision: str,
    reason: str,
    approved_amount: Optional[int] = None,
    tenure_months: Optional[int] = None,
    approved_interest_rate: Optional[float] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(REQUIRED_ROLES["make_decision"])),
):
    """Apply final decision and persist decision record."""
    try:
        app_id = uuid.UUID(application_id)
        actor_id = uuid.UUID(current_user.user_id)
        decision_enum = _parse_decision(decision)
        if not decision_enum:
            raise HTTPException(status_code=400, detail="Invalid decision value")

        application = db.query(LoanApplication).filter(LoanApplication.id == app_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        application.final_decision = decision_enum
        application.decision_date = datetime.utcnow()
        application.decision_reason = reason
        application.decided_by = actor_id
        if decision_enum == DecisionType.APPROVED:
            application.status = ApplicationStatus.APPROVED
        elif decision_enum == DecisionType.REJECTED:
            application.status = ApplicationStatus.REJECTED
        else:
            application.status = ApplicationStatus.HOLD

        amount = approved_amount if approved_amount is not None else application.requested_amount
        months = tenure_months if tenure_months is not None else application.requested_tenure_months
        rate = approved_interest_rate if approved_interest_rate is not None else 18.0
        emi = _safe_emi(amount, rate, months)

        db.add(
            Decision(
                application_id=app_id,
                decision_type=decision_enum,
                decision_date=datetime.utcnow(),
                decided_by_user_id=actor_id,
                reason=reason,
                approved_amount=amount if decision_enum == DecisionType.APPROVED else None,
                approved_tenure_months=months if decision_enum == DecisionType.APPROVED else None,
                approved_interest_rate=rate if decision_enum == DecisionType.APPROVED else None,
                estimated_emi=emi if decision_enum == DecisionType.APPROVED else None,
                is_override=False,
            )
        )

        audit = AuditService(db)
        audit.log_event(
            "decision_made",
            actor_id=actor_id,
            application_id=app_id,
            decision=decision_enum.value,
            decision_reason=reason,
        )
        db.commit()
        return {"status": "success", "decision": decision_enum.value, "application_id": application_id}
    except ValueError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid id format")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error making decision: {e}")
        raise HTTPException(status_code=500, detail="Failed to make decision")


@router.post("/applications/{application_id}/override")
def override_decision(
    application_id: str,
    override_decision: str,
    justification: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(REQUIRED_ROLES["override_decision"])),
):
    """Override decision with mandatory justification and audit record."""
    try:
        if not justification or len(justification.strip()) < 50:
            raise HTTPException(status_code=400, detail="Justification must be at least 50 characters")

        app_id = uuid.UUID(application_id)
        actor_id = uuid.UUID(current_user.user_id)
        decision_enum = _parse_decision(override_decision)
        if not decision_enum:
            raise HTTPException(status_code=400, detail="Invalid override decision value")

        application = db.query(LoanApplication).filter(LoanApplication.id == app_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        application.final_decision = decision_enum
        application.decision_date = datetime.utcnow()
        application.decision_overridden = True
        application.override_reason = justification
        application.override_by = actor_id
        application.override_at = datetime.utcnow()

        db.add(
            Decision(
                application_id=app_id,
                decision_type=decision_enum,
                decision_date=datetime.utcnow(),
                decided_by_user_id=actor_id,
                reason=f"Override: {justification}",
                is_override=True,
                override_reason=justification,
            )
        )

        audit = AuditService(db)
        audit.log_event(
            "override_applied",
            actor_id=actor_id,
            application_id=app_id,
            decision=decision_enum.value,
            decision_reason=justification,
            input_snapshot={"override_decision": decision_enum.value},
        )
        db.commit()
        return {"status": "success", "override_applied": True, "application_id": application_id}
    except ValueError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid id format")
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error overriding decision: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply override")


@router.get("/dashboard/kpis")
def get_dashboard_kpis(
    days: int = Query(30, description="Time window in days"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(["analyst", "senior_analyst", "risk_manager", "admin"])),
):
    """Get dashboard KPIs from application and decision data."""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        total_apps = db.query(func.count(LoanApplication.id)).filter(LoanApplication.created_at >= cutoff_date).scalar() or 0
        approved = db.query(func.count(LoanApplication.id)).filter(
            and_(LoanApplication.created_at >= cutoff_date, LoanApplication.final_decision == DecisionType.APPROVED)
        ).scalar() or 0
        rejected = db.query(func.count(LoanApplication.id)).filter(
            and_(LoanApplication.created_at >= cutoff_date, LoanApplication.final_decision == DecisionType.REJECTED)
        ).scalar() or 0
        held = db.query(func.count(LoanApplication.id)).filter(
            and_(LoanApplication.created_at >= cutoff_date, LoanApplication.final_decision == DecisionType.HOLD)
        ).scalar() or 0
        approval_rate = (approved / total_apps * 100) if total_apps else 0

        avg_score = db.query(func.avg(LoanApplication.credit_score)).filter(LoanApplication.created_at >= cutoff_date).scalar() or 0
        avg_pd = db.query(func.avg(LoanApplication.probability_of_default)).filter(LoanApplication.created_at >= cutoff_date).scalar() or 0

        total_approved_amount = db.query(func.sum(Decision.approved_amount)).join(
            LoanApplication, Decision.application_id == LoanApplication.id
        ).filter(
            and_(LoanApplication.created_at >= cutoff_date, Decision.decision_type == DecisionType.APPROVED)
        ).scalar() or 0

        high_fraud_apps = db.query(func.count(LoanApplication.id)).filter(
            and_(LoanApplication.created_at >= cutoff_date, LoanApplication.fraud_score > 0.6)
        ).scalar() or 0

        return {
            "period_days": days,
            "total_applications": int(total_apps),
            "decisions": {
                "approved": int(approved),
                "rejected": int(rejected),
                "held": int(held),
                "approval_rate_pct": round(approval_rate, 1),
            },
            "model_metrics": {
                "avg_credit_score": round(float(avg_score), 1),
                "avg_probability_of_default": round(float(avg_pd), 4),
            },
            "portfolio": {
                "total_approved_amount_inr": int(total_approved_amount),
                "avg_approved_amount_inr": int(total_approved_amount / approved) if approved else 0,
            },
            "fraud_detection": {
                "high_fraud_flagged": int(high_fraud_apps),
                "fraud_detection_rate_pct": round((high_fraud_apps / total_apps * 100), 1) if total_apps else 0,
            },
        }
    except Exception as e:
        logger.error(f"Error computing KPIs: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute dashboard KPIs")


@router.get("/fairness/report")
def get_fairness_report(
    days: int = Query(30),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(["risk_manager", "admin"])),
):
    """Return fairness monitoring report."""
    try:
        return FairnessMonitor(db).generate_fairness_report(time_window_days=days)
    except Exception as e:
        logger.error(f"Error generating fairness report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate fairness report")


@router.get("/portfolio/risk")
def get_portfolio_risk(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(["risk_manager", "admin"])),
):
    """Run portfolio simulation from approved applications."""
    try:
        approved_loans = db.query(LoanApplication).filter(LoanApplication.final_decision == DecisionType.APPROVED).all()
        if not approved_loans:
            return {"warning": "No approved loans for portfolio analysis"}

        portfolio = []
        for loan in approved_loans:
            latest_decision = None
            if loan.decisions:
                latest_decision = sorted(loan.decisions, key=lambda d: d.decision_date or datetime.min)[-1]
            portfolio.append(
                {
                    "id": str(loan.id),
                    "amount": float(
                        latest_decision.approved_amount
                        if latest_decision and latest_decision.approved_amount
                        else loan.requested_amount
                    ),
                    "probability_of_default": float(loan.probability_of_default or 0.2),
                    "lgd": 0.6,
                    "user_category": loan.user.user_category.value if loan.user and loan.user.user_category else "unknown",
                    "issued_date": loan.created_at,
                }
            )

        simulator = MonteCarloPortfolioSimulator(portfolio, n_simulations=10000)
        return {
            "simulation_results": simulator.simulate(),
            "portfolio_statistics": simulator.compute_portfolio_statistics(),
            "concentration_risk": simulator.identify_concentration_risk(),
        }
    except Exception as e:
        logger.error(f"Error computing portfolio risk: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute portfolio risk")


@router.get("/audit-logs/{application_id}")
def get_audit_logs(
    application_id: str,
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(REQUIRED_ROLES["view_audit_logs"])),
):
    """Return audit events for an application."""
    try:
        app_id = uuid.UUID(application_id)
        logs = (
            db.query(AuditLog)
            .filter(AuditLog.application_id == app_id)
            .order_by(desc(AuditLog.event_timestamp))
            .limit(limit)
            .all()
        )

        return {
            "application_id": application_id,
            "total_log_entries": len(logs),
            "logs": [
                {
                    "event_id": str(log.event_id),
                    "event_type": log.event_type,
                    "timestamp": log.event_timestamp.isoformat(),
                    "actor_id": str(log.actor_id) if log.actor_id else None,
                    "input_snapshot": log.input_snapshot,
                    "model_output": log.model_output,
                    "policy_results": log.policy_results,
                    "decision_reason": log.decision_reason,
                }
                for log in logs
            ],
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid application_id")
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch audit logs")
