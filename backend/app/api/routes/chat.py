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
from app.models.models import LoanApplication, ChatHistory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


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
        
        # Get or create chat history
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
            
            # Get existing chat history
            chat_history = db.query(ChatHistory).filter(
                ChatHistory.application_id == application_id
            ).order_by(ChatHistory.created_at).all()
            
            # Convert to OpenAI format
            conversation = [
                {
                    'role': 'user' if ch.sender == 'user' else 'assistant',
                    'content': ch.message
                }
                for ch in chat_history[-10:]  # Last 10 messages only
            ]
            
            # Prepare user context
            user_context = {
                'user_category': app.user_category,
                'credit_score': app.credit_score or 500,
                'application_status': app.final_decision or 'submitted',
                'top_positive_factors': app.top_positive_factors or [],
                'top_negative_factors': app.top_negative_factors or []
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
        
        # Store in database if application_id provided
        if application_id:
            # Store user message
            user_chat = ChatHistory(
                application_id=application_id,
                sender='user',
                message=message
            )
            db.add(user_chat)
            
            # Store bot response
            bot_chat = ChatHistory(
                application_id=application_id,
                sender='assistant',
                message=response_text
            )
            db.add(bot_chat)
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
        
        # Get chat history
        chats = db.query(ChatHistory).filter(
            ChatHistory.application_id == application_id
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
                for chat in reversed(chats)  # Reverse to show chronological order
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
        
        # Delete all chats
        db.query(ChatHistory).filter(
            ChatHistory.application_id == application_id
        ).delete()
        
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
