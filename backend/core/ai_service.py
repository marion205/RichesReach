# core/ai_service.py
import os
from django.conf import settings
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import openai, but don't fail if it's not available
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. AI features will use fallback responses.")

class AIService:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
        self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo')
        self.max_tokens = getattr(settings, 'OPENAI_MAX_TOKENS', 1000)
        
        if self.api_key and OPENAI_AVAILABLE:
            openai.api_key = self.api_key
        else:
            logger.warning("OpenAI API key not found or package not available. AI features will use fallback responses.")
    
    def get_chat_response(self, messages: List[Dict], user_context: Optional[str] = None) -> Dict:
        """
        Get a response from OpenAI's chat completion API
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            user_context: Optional user context information
            
        Returns:
            Dictionary containing response content, confidence, and token usage
        """
        if not self.api_key or not OPENAI_AVAILABLE:
            return self._get_fallback_response(messages[-1]['content'] if messages else "")
        
        try:
            # Add system context if provided
            system_messages = []
            if user_context:
                system_messages.append({
                    "role": "system",
                    "content": f"You are a helpful financial advisor. User context: {user_context}"
                })
            
            # Prepare messages for OpenAI
            openai_messages = system_messages + messages
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=openai_messages,
                max_tokens=self.max_tokens,
                temperature=0.7
            )
            
            return {
                "content": response.choices[0].message.content,
                "confidence": 0.9,  # OpenAI doesn't provide confidence scores
                "tokens_used": response.usage.total_tokens,
                "model_used": self.model
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return self._get_fallback_response(messages[-1]['content'] if messages else "")
    
    def _get_fallback_response(self, user_message: str) -> Dict:
        """Fallback response when OpenAI is not available"""
        return {
            "content": f"I'm currently in offline mode. You asked: '{user_message}'. "
                       f"Here are some general financial tips:\n"
                       f"• Always diversify your investments\n"
                       f"• Consider your time horizon and risk tolerance\n"
                       f"• Research fees and expenses\n"
                       f"• Visit investor.gov for educational resources",
            "confidence": 0.5,
            "tokens_used": 0,
            "model_used": "fallback"
        }
    
    def generate_session_title(self, first_message: str) -> str:
        """Generate a title for a chat session based on the first message"""
        if not self.api_key or not OPENAI_AVAILABLE:
            return "Financial Chat Session"
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Generate a short, descriptive title (max 50 chars) for a financial chat session based on the user's first message."},
                    {"role": "user", "content": f"First message: {first_message}"}
                ],
                max_tokens=20,
                temperature=0.3
            )
            
            title = response.choices[0].message.content.strip()
            # Clean up the title
            title = title.replace('"', '').replace("'", "")
            if len(title) > 50:
                title = title[:47] + "..."
            return title
            
        except Exception as e:
            logger.error(f"Error generating title: {str(e)}")
            return "Financial Chat Session"
