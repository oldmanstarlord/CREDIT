"""
Chat endpoint: Chatbot assistant for user portal.

Provides conversational help to applicants about their credit score,
loan application process, and ways to improve eligibility.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import logging
import os

from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.services.chatbot_service import ChatbotService
from app.models.models import LoanApplication

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

_CHAT_MEMORY: Dict[str, List[Dict[str, str]]] = {}


def get_chatbot_service():
    """Dependency: Get initialized chatbot service"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    return ChatbotService(api_key=api_key)


@router.post("/message")
def send_chat_message(
    message: str,
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
        # Validate message
        if not message or len(message.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        if len(message) > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message too long (max 1000 characters)"
            )
        
        # Build optional application context
        if application_id:
            app = db.query(LoanApplication).filter(
                LoanApplication.id == application_id,
                LoanApplication.user_id == current_user.sub
            ).first()
            
            if not app:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Application not found or access denied"
                )
            
            # Read in-memory conversation (fallback when ChatHistory table is not present)
            conversation = _CHAT_MEMORY.get(str(application_id), [])[-10:]
            
            # Prepare user context
            user_context = {
                'user_category': app.user_category,
                'credit_score': app.credit_score or 500,
                'application_status': app.final_decision or 'submitted',
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
        response_text, updated_conversation = chatbot.chat(
            message, user_context, conversation
        )
        
        # Get suggestions
        suggestions = chatbot.suggest_next_actions(user_context)
        
        # Store in in-memory history if application_id provided
        if application_id:
            _CHAT_MEMORY[str(application_id)] = updated_conversation[-20:]
        
        # Confidence score based on message length and context richness
        confidence = min(
            0.95,
            0.6 + (len(user_context.get('top_positive_factors', [])) * 0.05)
        )
        
        return {
            'response': response_text,
            'confidence': round(confidence, 2),
            'suggestions': suggestions[:3],  # Top 3 suggestions
            'application_id': application_id,
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
        app = db.query(LoanApplication).filter(
            LoanApplication.id == application_id,
            LoanApplication.user_id == current_user.sub
        ).first()
        
        if not app:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        chats = _CHAT_MEMORY.get(str(application_id), [])[-limit:]

        return {
            'application_id': application_id,
            'message_count': len(chats),
            'messages': [
                {
                    'id': str(idx + 1),
                    'sender': chat.get('role', 'assistant'),
                    'message': chat.get('content', ''),
                    'timestamp': datetime.utcnow().isoformat()
                }
                for idx, chat in enumerate(chats)
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
        app = db.query(LoanApplication).filter(
            LoanApplication.id == application_id,
            LoanApplication.user_id == current_user.sub
        ).first()
        
        if not app:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Delete in-memory history
        _CHAT_MEMORY.pop(str(application_id), None)
        
        return {'status': 'success', 'message': 'Chat history cleared'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear chat history"
        )
