"""
Chat endpoint: Chatbot assistant for user portal.

Provides conversational help to applicants about their credit score,
loan application process, and ways to improve eligibility.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user, TokenData
from app.services.chatbot_service import ChatbotService
from app.models.models import LoanApplication, ChatHistory
from app.schemas import ChatMessageRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


def get_chatbot_service():
    """Dependency: Get initialized chatbot service with configured provider."""
    provider = (settings.LLM_PROVIDER or "openrouter").lower()
    openrouter_key = (settings.OPENROUTER_API_KEY or "").strip()
    openai_key = (settings.OPENAI_API_KEY or "").strip()
    fallback_models = [
        model.strip()
        for model in (settings.OPENROUTER_FALLBACK_MODELS or "").split(",")
        if model.strip()
    ]

    if provider == "openrouter":
        if not openrouter_key and openai_key:
            logger.warning("LLM_PROVIDER=openrouter but OPENROUTER_API_KEY missing; falling back to OpenAI provider")
            return ChatbotService(
                api_key=openai_key,
                model=settings.OPENAI_MODEL,
                base_url=settings.OPENAI_BASE_URL,
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS,
            )
        if not openrouter_key and not openai_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM is not configured. Set OPENROUTER_API_KEY or OPENAI_API_KEY and restart backend.",
            )
        return ChatbotService(
            api_key=openrouter_key,
            model=settings.OPENROUTER_MODEL,
            base_url=settings.OPENROUTER_BASE_URL,
            site_url=settings.OPENROUTER_SITE_URL,
            app_name=settings.OPENROUTER_APP_NAME,
            fallback_models=fallback_models,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )

    if not openai_key and openrouter_key:
        logger.warning("LLM_PROVIDER=openai but OPENAI_API_KEY missing; falling back to OpenRouter provider")
        return ChatbotService(
            api_key=openrouter_key,
            model=settings.OPENROUTER_MODEL,
            base_url=settings.OPENROUTER_BASE_URL,
            site_url=settings.OPENROUTER_SITE_URL,
            app_name=settings.OPENROUTER_APP_NAME,
            fallback_models=fallback_models,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )
    if not openai_key and not openrouter_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM is not configured. Set OPENROUTER_API_KEY or OPENAI_API_KEY and restart backend.",
        )

    return ChatbotService(
        api_key=openai_key,
        model=settings.OPENAI_MODEL,
        base_url=settings.OPENAI_BASE_URL,
        temperature=settings.OPENAI_TEMPERATURE,
        max_tokens=settings.OPENAI_MAX_TOKENS,
    )


@router.post("/message")
def send_chat_message(
    payload: Optional[ChatMessageRequest] = None,
    message: Optional[str] = None,
    application_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    chatbot: ChatbotService = Depends(get_chatbot_service)
):
    """
    Send a message to the chatbot and get response.
    
    Returns:
        {
            'response': str,
            'confidence': float (0-1, how confident the bot is),
            'suggestions': [str] (next action suggestions),
            'conversation_id': str
        }
    """
    try:
        resolved_message = payload.message if payload else message
        resolved_application_id = payload.application_id if payload and payload.application_id is not None else application_id

        # Validate message
        if not resolved_message or len(resolved_message.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        if len(resolved_message) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message too long (max 1000 characters)"
            )
        
        # Build optional application context
        if resolved_application_id:
            app_id = uuid.UUID(resolved_application_id)
            user_id = uuid.UUID(current_user.user_id)
            app = db.query(LoanApplication).filter(
                LoanApplication.id == app_id,
                LoanApplication.user_id == user_id
            ).first()
            
            if not app:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Application not found or access denied"
                )
            
            # Read persisted conversation
            chat_history = db.query(ChatHistory).filter(
                ChatHistory.application_id == app_id,
                ChatHistory.user_id == user_id
            ).order_by(ChatHistory.created_at.asc()).all()
            conversation = [
                {
                    'role': ch.sender,
                    'content': ch.message
                }
                for ch in chat_history[-10:]
            ]
            
            # Prepare user context from schema-valid fields.
            category_value = None
            if app.user and app.user.user_category:
                category_value = app.user.user_category.value
            elif app.category_specific_data and app.category_specific_data.user_category:
                category_value = app.category_specific_data.user_category.value

            app_status = app.final_decision.value if app.final_decision else app.status.value

            user_context = {
                'user_category': category_value or 'unknown',
                'credit_score': app.credit_score or 500,
                'application_status': app_status,
                'top_positive_factors': getattr(app, 'top_positive_factors', []) or [],
                'top_negative_factors': getattr(app, 'top_negative_factors', []) or []
            }
        else:
            # No application context
            conversation = []
            user_context = {
                'user_category': 'unknown',
                'credit_score': 500,
                'application_status': 'new_user'
            }
        
        # Get chatbot response
        response_text, _updated_conversation = chatbot.chat(
            resolved_message, user_context, conversation
        )
        
        # Get suggestions
        suggestions = chatbot.suggest_next_actions(user_context)
        
        # Store in persistent history if application_id provided
        if resolved_application_id:
            app_id = uuid.UUID(resolved_application_id)
            user_id = uuid.UUID(current_user.user_id)
            db.add(
                ChatHistory(
                    application_id=app_id,
                    user_id=user_id,
                    sender='user',
                    message=resolved_message,
                )
            )
            db.add(
                ChatHistory(
                    application_id=app_id,
                    user_id=user_id,
                    sender='assistant',
                    message=response_text,
                )
            )
            db.commit()
        
        # Confidence score based on message length and context richness
        confidence = min(
            0.95,
            0.6 + (len(user_context.get('top_positive_factors', [])) * 0.05)
        )
        
        return {
            'response': response_text,
            'confidence': round(confidence, 2),
            'suggestions': suggestions[:3],  # Top 3 suggestions
            'application_id': resolved_application_id,
            'llm_provider': settings.LLM_PROVIDER,
            'llm_model': chatbot.last_model_used or 'rule_based_fallback',
            'fallback_used': chatbot.used_fallback_response,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )


@router.get("/history/{application_id}")
def get_chat_history(
    application_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get chat history for application"""
    try:
        # Verify ownership
        app_id = uuid.UUID(application_id)
        user_id = uuid.UUID(current_user.user_id)
        app = db.query(LoanApplication).filter(
            LoanApplication.id == app_id,
            LoanApplication.user_id == user_id
        ).first()
        
        if not app:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        chats = db.query(ChatHistory).filter(
            ChatHistory.application_id == app_id,
            ChatHistory.user_id == user_id
        ).order_by(ChatHistory.created_at.desc()).limit(limit).all()

        return {
            'application_id': application_id,
            'message_count': len(chats),
            'messages': [
                {
                    'id': str(chat.id),
                    'sender': chat.sender,
                    'message': chat.message,
                    'timestamp': chat.created_at.isoformat()
                }
                for chat in reversed(chats)
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch chat history"
        )


@router.delete("/history/{application_id}")
def clear_chat_history(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Clear chat history (user can delete their own conversation)"""
    try:
        # Verify ownership
        app_id = uuid.UUID(application_id)
        user_id = uuid.UUID(current_user.user_id)
        app = db.query(LoanApplication).filter(
            LoanApplication.id == app_id,
            LoanApplication.user_id == user_id
        ).first()
        
        if not app:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        db.query(ChatHistory).filter(
            ChatHistory.application_id == app_id,
            ChatHistory.user_id == user_id
        ).delete(synchronize_session=False)
        db.commit()
        
        return {'status': 'success', 'message': 'Chat history cleared'}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear chat history"
        )
