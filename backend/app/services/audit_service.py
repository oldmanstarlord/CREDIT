"""Audit logging service for critical user and decision events."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.models import AuditLog, DecisionType


class AuditService:
    """Persist immutable-style audit records for key workflow actions."""

    def __init__(self, db: Session):
        self.db = db

    def log_event(
        self,
        event_type: str,
        *,
        user_id: Optional[uuid.UUID] = None,
        actor_id: Optional[uuid.UUID] = None,
        application_id: Optional[uuid.UUID] = None,
        model_version: Optional[str] = None,
        model_output: Optional[Dict[str, Any]] = None,
        policy_results: Optional[Dict[str, Any]] = None,
        decision: Optional[str] = None,
        decision_reason: Optional[str] = None,
        input_snapshot: Optional[Dict[str, Any]] = None,
    ) -> None:
        final_decision = None
        if decision:
            try:
                final_decision = DecisionType(decision)
            except Exception:
                final_decision = None

        audit = AuditLog(
            id=uuid.uuid4(),
            event_id=uuid.uuid4(),
            application_id=application_id,
            user_id=user_id,
            actor_id=actor_id,
            event_type=event_type,
            event_timestamp=datetime.utcnow(),
            input_snapshot=input_snapshot,
            model_version=model_version,
            model_output=model_output,
            policy_results=policy_results,
            final_decision=final_decision,
            decision_reason=decision_reason,
        )
        self.db.add(audit)