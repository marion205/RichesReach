"""
Django Assistant Views
Provides Django REST endpoints for the AI Assistant functionality
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django.conf import settings

from .ai_service import AIService

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class AssistantQueryView(View):
    """Handle assistant query requests"""
    
    def post(self, request):
        """Process assistant query request"""
        try:
            data = json.loads(request.body)
            prompt = data.get('prompt', '')
            user_id = data.get('user_id', 'anonymous')
            context = data.get('context', {})
            market_context = data.get('market_context', {})
            
            if not prompt:
                return JsonResponse({'error': 'Prompt is required'}, status=400)
            
            # Check if OpenAI is enabled and has a real API key
            use_openai = getattr(settings, 'USE_OPENAI', False)
            openai_key = getattr(settings, 'OPENAI_API_KEY', '')
            
            if use_openai and openai_key and not openai_key.startswith('sk-proj-mock'):
                # Use real AI service
                try:
                    ai_service = AIService()
                    
                    # Create a comprehensive prompt for financial assistant
                    system_prompt = """You are a helpful financial assistant for RichesReach, a comprehensive financial platform. 
                    You help users with:
                    - Investment advice and portfolio analysis
                    - Financial planning and budgeting
                    - Market insights and trends
                    - Educational content about personal finance
                    - Answering questions about financial concepts
                    
                    Always provide helpful, accurate, and educational responses. If you're unsure about something, 
                    recommend consulting with a financial advisor for personalized advice."""
                    
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                    
                    ai_response = ai_service.get_chat_response(messages, user_context=f"User ID: {user_id}")
                    
                    response = {
                        'answer': ai_response.get('content', 'I apologize, but I could not generate a response at this time.'),
                        'response': ai_response.get('content', 'I apologize, but I could not generate a response at this time.'),
                        'model': ai_response.get('model', 'unknown'),
                        'timestamp': timezone.now().isoformat(),
                        'user_id': user_id,
                        'source': 'openai'
                    }
                    
                except Exception as ai_error:
                    logger.warning(f"AI service failed, falling back to mock: {ai_error}")
                    # Fall back to mock response
                    response = {
                        'answer': f"I understand you're asking: '{prompt}'. This is a mock response from the AI assistant. The AI service is temporarily unavailable.",
                        'response': f"I understand you're asking: '{prompt}'. This is a mock response from the AI assistant. The AI service is temporarily unavailable.",
                        'model': 'mock-model',
                        'timestamp': timezone.now().isoformat(),
                        'user_id': user_id,
                        'source': 'mock-fallback'
                    }
            else:
                # Use mock response when OpenAI is disabled or using mock key
                response = {
                    'answer': f"I understand you're asking: '{prompt}'. This is a mock response from the AI assistant. To enable real AI responses, please configure a valid OpenAI API key.",
                    'response': f"I understand you're asking: '{prompt}'. This is a mock response from the AI assistant. To enable real AI responses, please configure a valid OpenAI API key.",
                    'model': 'mock-model',
                    'timestamp': timezone.now().isoformat(),
                    'user_id': user_id,
                    'source': 'mock'
                }
            
            return JsonResponse(response)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error in assistant query: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
