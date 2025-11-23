"""
REST API Views for Voice/TTS Services
"""
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class VoicesListView(View):
    """
    GET /api/voices/
    Returns available TTS voices
    """
    
    def get(self, request):
        try:
            logger.info('🎤 [Voices API] Fetching available voices')
            
            # Return default voices
            voices = {
                'voices': [
                    {
                        'id': 'default_en',
                        'name': 'Default English',
                        'locale': 'en-US',
                        'gender': 'neutral',
                        'provider': 'polly'
                    },
                    {
                        'id': 'default_es',
                        'name': 'Default Spanish',
                        'locale': 'es-ES',
                        'gender': 'neutral',
                        'provider': 'polly'
                    },
                    {
                        'id': 'finance_expert',
                        'name': 'Finance Expert',
                        'locale': 'en-US',
                        'gender': 'male',
                        'provider': 'polly'
                    },
                    {
                        'id': 'friendly_advisor',
                        'name': 'Friendly Advisor',
                        'locale': 'en-US',
                        'gender': 'female',
                        'provider': 'polly'
                    }
                ]
            }
            
            logger.info(f'✅ [Voices API] Returning {len(voices["voices"])} voices')
            return JsonResponse(voices)
            
        except Exception as e:
            logger.error(f'❌ [Voices API] Error: {e}', exc_info=True)
            return JsonResponse({
                'error': str(e)
            }, status=500)

