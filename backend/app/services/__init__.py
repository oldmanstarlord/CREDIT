"""
Service layer initialization
Exports all service classes for easy importing
"""

from app.services.fraud_service import FraudCheckService
from app.services.audit_service import AuditService
from app.services.policy_engine import PolicyEngine
from app.services.chatbot_service import ChatbotService
from app.services.fairness_service import FairnessMonitor
from app.services.portfolio_service import MonteCarloPortfolioSimulator
from app.services.trust_service import TrustService
from app.services.aws_service import AWSService
from app.services.notification_service import NotificationService

# Backward-compatible aliases used by older imports.
FairnessService = FairnessMonitor
PortfolioService = MonteCarloPortfolioSimulator

__all__ = [
    "FraudCheckService",
    "AuditService",
    "PolicyEngine",
    "ChatbotService",
    "FairnessService",
    "PortfolioService",
    "TrustService",
    "AWSService",
    "NotificationService",
]

