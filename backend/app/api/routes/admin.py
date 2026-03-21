"""
Admin routes: Bank operations portal for analysts, risk managers, and admins.

Tier 1 - Analyst: View applications, add notes, see scores
Tier 2 - Senior Analyst: Recommend decisions, request overrides  
Tier 3 - Risk Manager: Approve/reject, override with justification
Tier 4 - Admin: Full access including policy configuration
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.models.models import LoanApplication, AuditLog
from app.services.audit_service import AuditService
from app.services.policy_engine import PolicyEngine
from app.services.fairness_service import FairnessMonitor
from app.services.portfolio_service import MonteCarloPortfolioSimulator

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

# Role-based access control
REQUIRED_ROLES = {
    'get_applications': ['analyst', 'senior_analyst', 'risk_manager', 'admin'],
    'get_application_detail': ['analyst', 'senior_analyst', 'risk_manager', 'admin'],
    'add_notes': ['analyst', 'senior_analyst', 'risk_manager', 'admin'],
    'recommend_decision': ['senior_analyst', 'risk_manager', 'admin'],
    'make_decision': ['risk_manager', 'admin'],
    'override_decision': ['risk_manager', 'admin'],
    'view_audit_logs': ['risk_manager', 'admin'],
    'manage_policy': ['admin'],
    'manage_users': ['admin']
}


def check_role(required_roles: List[str]):
    """Dependency: Check if user has required role"""
    def role_checker(current_user: TokenData = Depends(get_current_user)):
        user_role = current_user.role if hasattr(current_user, 'role') else 'analyst'
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' not authorized for this action"
            )
        return current_user
    return role_checker


# ─────────────────────────────────────────────────────────────────
# APPLICATION PIPELINE ENDPOINTS
# ─────────────────────────────────────────────────────────────────

@router.get("/applications", response_model=Dict[str, Any])
def get_applications(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(REQUIRED_ROLES['get_applications'])),
    stage: Optional[str] = Query(None, description="pre_screen|ml_scored|policy_checked|decided"),
    status_filter: Optional[str] = Query(None, description="approved|rejected|held"),
    category: Optional[str] = Query(None),
    fraud_score_min: float = Query(0.0),
    fraud_score_max: float = Query(1.0),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
):
    """
    Get paginated list of applications with filtering.
    
    Analysts see: all applications in their assigned stage
    Risk managers see: all applications
    """
    try:
        query = db.query(LoanApplication)
        
        # Filter by stage
        if stage:
            stage_map = {
                'pre_screen': 'pre_screened',
                'ml_scored': 'ml_scored',
                'policy_checked': 'policy_checked',
                'decided': 'decided'
            }
            query = query.filter(LoanApplication.stage == stage_map.get(stage))
        
        # Filter by status
        if status_filter:
            query = query.filter(LoanApplication.final_decision == status_filter)
        
        # Filter by category
        if category:
            query = query.filter(LoanApplication.user_category == category)
        
        # Filter by fraud score range
        query = query.filter(
            and_(
                LoanApplication.fraud_score >= fraud_score_min,
                LoanApplication.fraud_score <= fraud_score_max
            )
        )
        
        # Count total
        total_count = query.count()
        
        # Sort and paginate
        sort_column = getattr(LoanApplication, sort_by, LoanApplication.created_at)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        applications = query.offset(offset).limit(limit).all()
        
        return {
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'count': len(applications),
            'applications': [
                {
                    'id': str(app.id),
                    'user_name': app.user.full_name if app.user else 'Unknown',
                    'category': app.user_category,
                    'created_at': app.created_at.isoformat(),
                    'fraud_score': app.fraud_score,
                    'credit_score': app.credit_score,
                    'probability_of_default': app.probability_of_default,
                    'requested_amount': app.requested_amount,
                    'final_decision': app.final_decision,
                    'stage': app.stage
                }
                for app in applications
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/applications/{application_id}", response_model=Dict[str, Any])
def get_application_detail(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(REQUIRED_ROLES['get_application_detail']))
):
    """Get full detailed view of single application"""
    try:
        application = db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Get audit log for this application
        audit_logs = db.query(AuditLog).filter(
            AuditLog.application_id == application_id
        ).order_by(desc(AuditLog.event_timestamp)).all()
        
        return {
            'id': str(application.id),
            'user': {
                'id': str(application.user_id),
                'name': application.user.full_name if application.user else '',
                'email': application.user.email if application.user else '',
                'phone': application.user.phone_number if application.user else ''
            },
            'category': application.user_category,
            'application_data': application.application_data or {},
            'fraud_check': {
                'fraud_score': application.fraud_score,
                'fraud_decision': application.fraud_decision,
                'fraud_details': application.fraud_check_details or {}
            },
            'ml_scoring': {
                'credit_score': application.credit_score,
                'probability_of_default': application.probability_of_default,
                'risk_band': application.risk_band,
                'shap_explanation': application.shap_explanation or {}
            },
            'policy_check': {
                'all_passed': application.policy_checks_passed,
                'details': application.policy_check_details or {}
            },
            'decision': {
                'final_decision': application.final_decision,
                'decision_timestamp': application.decided_at.isoformat() if application.decided_at else None,
                'decision_reason': application.decision_reason,
                'override_flag': application.override_flag,
                'override_justification': application.override_justification
            },
            'loan_terms': {
                'requested_amount': application.requested_amount,
                'approved_amount': application.approved_amount,
                'interest_rate_min': application.interest_rate_min,
                'interest_rate_max': application.interest_rate_max,
                'tenure_months': application.tenure_months,
                'estimated_emi': application.estimated_emi
            },
            'audit_trail': [
                {
                    'event_type': log.event_type,
                    'timestamp': log.event_timestamp.isoformat(),
                    'actor': log.actor_id,
                    'details': log.details or {}
                }
                for log in audit_logs[:20]  # Last 20 events
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching application detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/applications/{application_id}/notes")
def add_notes(
    application_id: str,
    note_text: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(REQUIRED_ROLES['add_notes']))
):
    """Add analyst notes to application"""
    try:
        application = db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Append note to notes field
        if not application.analyst_notes:
            application.analyst_notes = []
        
        application.analyst_notes.append({
            'timestamp': datetime.utcnow().isoformat(),
            'actor': str(current_user.sub),
            'text': note_text
        })
        
        db.commit()
        
        # Log to audit trail
        audit = AuditService(db)
        audit.log_event(
            'note_added',
            actor_id=current_user.sub,
            application_id=application_id,
            input_snapshot={'note': note_text}
        )
        
        return {'status': 'success', 'note_added': True}
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/applications/{application_id}/decide")
def make_decision(
    application_id: str,
    decision: str,
    reason: str,
    approved_amount: Optional[int] = None,
    tenure_months: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(REQUIRED_ROLES['make_decision']))
):
    """
    Make final approval/rejection decision.
    
    Decision options: 'approved', 'rejected', 'held'
    """
    try:
        if decision not in ['approved', 'rejected', 'held']:
            raise HTTPException(status_code=400, detail="Invalid decision value")
        
        application = db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Update application
        application.final_decision = decision
        application.decided_at = datetime.utcnow()
        application.decision_reason = reason
        
        if decision == 'approved':
            application.approved_amount = approved_amount or application.requested_amount
            application.tenure_months = tenure_months or 18
            
            # Compute EMI
            rate = (application.interest_rate_min + application.interest_rate_max) / 2 / 100 / 12
            n = tenure_months or 18
            application.estimated_emi = (application.approved_amount * rate * (1 + rate)**n) / \
                                        ((1 + rate)**n - 1)
        
        db.commit()
        
        # Log to audit
        audit = AuditService(db)
        audit.log_event(
            'decision_made',
            actor_id=current_user.sub,
            application_id=application_id,
            decision=decision,
            decision_reason=reason
        )
        
        return {
            'status': 'success',
            'decision': decision,
            'application_id': application_id
        }
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error making decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/applications/{application_id}/override")
def override_decision(
    application_id: str,
    override_decision: str,
    justification: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(REQUIRED_ROLES['override_decision']))
):
    """
    Override model decision (risk_manager+ only).
    Justification is MANDATORY and stored in audit trail.
    """
    try:
        if not justification or len(justification) < 50:
            raise HTTPException(
                status_code=400,
                detail="Justification required and must be at least 50 characters"
            )
        
        application = db.query(LoanApplication).filter(
            LoanApplication.id == application_id
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        
        # Record override
        application.override_flag = True
        application.override_justification = justification
        application.final_decision = override_decision
        application.decided_at = datetime.utcnow()
        
        db.commit()
        
        # Log to audit with override details
        audit = AuditService(db)
        audit.log_event(
            'override_applied',
            actor_id=current_user.sub,
            application_id=application_id,
            input_snapshot={
                'override_decision': override_decision,
                'original_decision': 'unknown',  # Would need to track
                'justification': justification
            }
        )
        
        return {
            'status': 'success',
            'override_applied': True,
            'application_id': application_id
        }
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error overriding decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# ANALYTICS & MONITORING ENDPOINTS
# ─────────────────────────────────────────────────────────────────

@router.get("/dashboard/kpis")
def get_dashboard_kpis(
    days: int = Query(30, description="Time window in days"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(['analyst', 'senior_analyst', 'risk_manager', 'admin']))
):
    """Get key performance indicators for admin dashboard"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Count applications by status
        total_apps = db.query(func.count(LoanApplication.id)).filter(
            LoanApplication.created_at >= cutoff_date
        ).scalar() or 0
        
        approved = db.query(func.count(LoanApplication.id)).filter(
            and_(
                LoanApplication.created_at >= cutoff_date,
                LoanApplication.final_decision == 'approved'
            )
        ).scalar() or 0
        
        rejected = db.query(func.count(LoanApplication.id)).filter(
            and_(
                LoanApplication.created_at >= cutoff_date,
                LoanApplication.final_decision == 'rejected'
            )
        ).scalar() or 0
        
        held = db.query(func.count(LoanApplication.id)).filter(
            and_(
                LoanApplication.created_at >= cutoff_date,
                LoanApplication.final_decision == 'held'
            )
        ).scalar() or 0
        
        approval_rate = (approved / total_apps * 100) if total_apps > 0 else 0
        
        # Average credit score
        avg_score = db.query(func.avg(LoanApplication.credit_score)).filter(
            LoanApplication.created_at >= cutoff_date
        ).scalar() or 0
        
        # Average PD
        avg_pd = db.query(func.avg(LoanApplication.probability_of_default)).filter(
            LoanApplication.created_at >= cutoff_date
        ).scalar() or 0
        
        # Portfolio stats
        total_approved_amount = db.query(func.sum(LoanApplication.approved_amount)).filter(
            and_(
                LoanApplication.created_at >= cutoff_date,
                LoanApplication.final_decision == 'approved'
            )
        ).scalar() or 0
        
        # Fraud detection rate
        high_fraud_apps = db.query(func.count(LoanApplication.id)).filter(
            and_(
                LoanApplication.created_at >= cutoff_date,
                LoanApplication.fraud_score > 0.6
            )
        ).scalar() or 0
        
        return {
            'period_days': days,
            'total_applications': total_apps,
            'decisions': {
                'approved': approved,
                'rejected': rejected,
                'held': held,
                'approval_rate_pct': round(approval_rate, 1)
            },
            'model_metrics': {
                'avg_credit_score': round(avg_score, 1),
                'avg_probability_of_default': round(avg_pd, 4)
            },
            'portfolio': {
                'total_approved_amount_inr': int(total_approved_amount),
                'avg_approved_amount_inr': int(total_approved_amount / approved) if approved > 0 else 0
            },
            'fraud_detection': {
                'high_fraud_flagged': high_fraud_apps,
                'fraud_detection_rate_pct': round(high_fraud_apps / total_apps * 100, 1) if total_apps > 0 else 0
            }
        }
    except Exception as e:
        logger.error(f"Error computing KPIs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fairness/report")
def get_fairness_report(
    days: int = Query(30),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(['risk_manager', 'admin']))
):
    """Get fairness monitoring report with disparate impact analysis"""
    try:
        monitor = FairnessMonitor(db)
        report = monitor.generate_fairness_report(time_window_days=days)
        return report
    except Exception as e:
        logger.error(f"Error generating fairness report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/risk")
def get_portfolio_risk(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(['risk_manager', 'admin']))
):
    """Get portfolio risk assessment via Monte Carlo simulation"""
    try:
        # Get all non-defaulted approved loans
        approved_loans = db.query(LoanApplication).filter(
            LoanApplication.final_decision == 'approved'
        ).all()
        
        if not approved_loans:
            return {'warning': 'No approved loans for portfolio analysis'}
        
        # Prepare portfolio data
        portfolio = [
            {
                'id': str(loan.id),
                'amount': float(loan.approved_amount or loan.requested_amount),
                'probability_of_default': float(loan.probability_of_default or 0.2),
                'lgd': 0.6,  # Default LGD
                'user_category': loan.user_category,
                'issued_date': loan.created_at
            }
            for loan in approved_loans
        ]
        
        # Run simulator
        simulator = MonteCarloPortfolioSimulator(portfolio, n_simulations=10000)
        
        results = simulator.simulate()
        stats = simulator.compute_portfolio_statistics()
        concentration = simulator.identify_concentration_risk()
        
        return {
            'simulation_results': results,
            'portfolio_statistics': stats,
            'concentration_risk': concentration
        }
    except Exception as e:
        logger.error(f"Error computing portfolio risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit-logs/{application_id}")
def get_audit_logs(
    application_id: str,
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(check_role(['risk_manager', 'admin']))
):
    """Get immutable audit trail for an application"""
    try:
        logs = db.query(AuditLog).filter(
            AuditLog.application_id == application_id
        ).order_by(desc(AuditLog.event_timestamp)).limit(limit).all()
        
        return {
            'application_id': application_id,
            'total_log_entries': len(logs),
            'logs': [
                {
                    'event_id': str(log.id),
                    'event_type': log.event_type,
                    'timestamp': log.event_timestamp.isoformat(),
                    'actor_id': str(log.actor_id) if log.actor_id else None,
                    'details': log.details or {}
                }
                for log in logs
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
