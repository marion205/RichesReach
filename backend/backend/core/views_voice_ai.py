"""
Voice AI API Views for RichesReach
Handles text-to-speech synthesis and voice AI interactions
"""

import os
import logging
from django.http import JsonResponse, FileResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
import json
import asyncio
from .voice_ai_service import voice_ai_service

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class VoiceAIView(View):
    """Main voice AI endpoint for text-to-speech synthesis"""
    
    async def post(self, request):
        """Synthesize speech from text"""
        try:
            data = json.loads(request.body)
            text = data.get('text', '').strip()
            voice = data.get('voice', 'default')
            speed = float(data.get('speed', 1.0))
            emotion = data.get('emotion', 'neutral')
            
            if not text:
                return JsonResponse({
                    'error': 'Text is required',
                    'success': False
                }, status=400)
            
            # Validate parameters
            if not 0.5 <= speed <= 2.0:
                speed = 1.0
            
            valid_emotions = ['neutral', 'confident', 'friendly', 'analytical', 'encouraging']
            if emotion not in valid_emotions:
                emotion = 'neutral'
            
            logger.info(f"🎤 TTS Request: '{text[:50]}...' with voice '{voice}'")
            
            # Synthesize speech
            audio_path = await voice_ai_service.synthesize_speech(
                text=text,
                voice=voice,
                speed=speed,
                emotion=emotion
            )
            
            if not audio_path:
                return JsonResponse({
                    'error': 'Failed to generate speech',
                    'success': False
                }, status=500)
            
            # Return audio file URL
            audio_filename = os.path.basename(audio_path)
            audio_url = f"/api/voice-ai/audio/{audio_filename}"
            
            return JsonResponse({
                'success': True,
                'audio_url': audio_url,
                'filename': audio_filename,
                'text': text,
                'voice': voice,
                'speed': speed,
                'emotion': emotion
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data',
                'success': False
            }, status=400)
        except Exception as e:
            logger.error(f"❌ Voice AI error: {e}")
            return JsonResponse({
                'error': 'Internal server error',
                'success': False
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class VoiceAIAudioView(View):
    """Serve generated audio files"""
    
    def get(self, request, filename):
        """Serve audio file"""
        try:
            # Security: only allow TTS files
            if not filename.startswith('tts_') or not filename.endswith('.wav'):
                return HttpResponse('File not found', status=404)
            
            audio_path = os.path.join(voice_ai_service.audio_output_dir, filename)
            
            if not os.path.exists(audio_path):
                return HttpResponse('File not found', status=404)
            
            # Serve file with proper headers
            response = FileResponse(
                open(audio_path, 'rb'),
                content_type='audio/wav'
            )
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            response['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Audio serving error: {e}")
            return HttpResponse('Error serving file', status=500)

@method_decorator(csrf_exempt, name='dispatch')
class VoiceAIVoicesView(View):
    """Get available voices and their properties"""
    
    async def get(self, request):
        """Get list of available voices"""
        try:
            voices = await voice_ai_service.get_available_voices()
            
            return JsonResponse({
                'success': True,
                'voices': voices,
                'default_voice': 'default',
                'supported_emotions': ['neutral', 'confident', 'friendly', 'analytical', 'encouraging'],
                'speed_range': {'min': 0.5, 'max': 2.0, 'default': 1.0}
            })
            
        except Exception as e:
            logger.error(f"❌ Voices API error: {e}")
            return JsonResponse({
                'error': 'Failed to get voices',
                'success': False
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class VoiceAIHealthView(View):
    """Health check for voice AI service"""
    
    async def get(self, request):
        """Check if voice AI service is healthy"""
        try:
            # Check if model is loaded
            model_status = "loaded" if voice_ai_service.model_loaded else "not_loaded"
            
            # Check output directory
            output_dir_exists = os.path.exists(voice_ai_service.audio_output_dir)
            
            # Check available disk space
            import shutil
            total, used, free = shutil.disk_usage(voice_ai_service.audio_output_dir)
            free_gb = free // (1024**3)
            
            health_status = "healthy" if (model_status == "loaded" and output_dir_exists) else "degraded"
            
            return JsonResponse({
                'success': True,
                'status': health_status,
                'model_status': model_status,
                'output_directory': output_dir_exists,
                'free_disk_space_gb': free_gb,
                'service': 'voice_ai',
                'version': '1.0.0'
            })
            
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return JsonResponse({
                'error': 'Health check failed',
                'success': False,
                'status': 'unhealthy'
            }, status=500)

# Async wrapper for Django views
def async_view(view_func):
    """Decorator to make Django views async"""
    def wrapper(request, *args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(view_func(request, *args, **kwargs))
        finally:
            loop.close()
    return wrapper

@method_decorator(csrf_exempt, name='dispatch')
class VoiceAIBatchView(View):
    """Batch voice AI endpoint for multiple text synthesis"""
    
    async def post(self, request):
        """Synthesize multiple texts in batch for efficiency"""
        try:
            data = json.loads(request.body)
            texts = data.get('texts', [])
            voice = data.get('voice', 'default')
            speed = float(data.get('speed', 1.0))
            emotion = data.get('emotion', 'neutral')
            
            if not texts or not isinstance(texts, list):
                return JsonResponse({
                    'error': 'Texts array is required',
                    'success': False
                }, status=400)
            
            if len(texts) > 10:  # Limit batch size
                return JsonResponse({
                    'error': 'Maximum 10 texts per batch',
                    'success': False
                }, status=400)
            
            # Validate parameters
            if not 0.5 <= speed <= 2.0:
                speed = 1.0
            
            valid_emotions = ['neutral', 'confident', 'friendly', 'analytical', 'encouraging']
            if emotion not in valid_emotions:
                emotion = 'neutral'
            
            logger.info(f"🎤 Batch TTS Request: {len(texts)} texts with voice '{voice}'")
            
            # Process texts in parallel
            import asyncio
            tasks = []
            for i, text in enumerate(texts):
                if text and text.strip():
                    task = voice_ai_service.synthesize_speech(
                        text=text.strip(),
                        voice=voice,
                        speed=speed,
                        emotion=emotion
                    )
                    tasks.append((i, task))
            
            # Wait for all synthesis to complete
            results = []
            for i, task in tasks:
                audio_path = await task
                if audio_path:
                    audio_filename = os.path.basename(audio_path)
                    audio_url = f"/api/voice-ai/audio/{audio_filename}"
                    results.append({
                        'index': i,
                        'success': True,
                        'audio_url': audio_url,
                        'filename': audio_filename,
                        'text': texts[i]
                    })
                else:
                    results.append({
                        'index': i,
                        'success': False,
                        'error': 'Failed to generate speech',
                        'text': texts[i]
                    })
            
            # Sort results by original index
            results.sort(key=lambda x: x['index'])
            
            return JsonResponse({
                'success': True,
                'results': results,
                'total_processed': len(results),
                'successful': len([r for r in results if r['success']]),
                'voice': voice,
                'speed': speed,
                'emotion': emotion
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data',
                'success': False
            }, status=400)
        except Exception as e:
            logger.error(f"❌ Batch Voice AI error: {e}")
            return JsonResponse({
                'error': 'Internal server error',
                'success': False
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class VoiceAIPreviewView(View):
    """Preview endpoint for testing voice settings"""
    
    async def post(self, request):
        """Generate a short preview of voice settings"""
        try:
            data = json.loads(request.body)
            voice = data.get('voice', 'default')
            speed = float(data.get('speed', 1.0))
            emotion = data.get('emotion', 'neutral')
            
            # Use a standard preview text
            preview_text = "Hello, I'm your AI financial advisor. I can help you understand market trends, analyze your portfolio, and provide personalized investment insights."
            
            logger.info(f"🎤 Voice Preview: voice '{voice}', speed {speed}, emotion '{emotion}'")
            
            # Synthesize preview
            audio_path = await voice_ai_service.synthesize_speech(
                text=preview_text,
                voice=voice,
                speed=speed,
                emotion=emotion
            )
            
            if not audio_path:
                return JsonResponse({
                    'error': 'Failed to generate preview',
                    'success': False
                }, status=500)
            
            # Return preview audio
            audio_filename = os.path.basename(audio_path)
            audio_url = f"/api/voice-ai/audio/{audio_filename}"
            
            return JsonResponse({
                'success': True,
                'audio_url': audio_url,
                'filename': audio_filename,
                'preview_text': preview_text,
                'voice': voice,
                'speed': speed,
                'emotion': emotion
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON data',
                'success': False
            }, status=400)
        except Exception as e:
            logger.error(f"❌ Voice Preview error: {e}")
            return JsonResponse({
                'error': 'Internal server error',
                'success': False
            }, status=500)

# Apply async wrapper to async views
VoiceAIView.post = async_view(VoiceAIView.post)
VoiceAIVoicesView.get = async_view(VoiceAIVoicesView.get)
VoiceAIHealthView.get = async_view(VoiceAIHealthView.get)
VoiceAIBatchView.post = async_view(VoiceAIBatchView.post)
VoiceAIPreviewView.post = async_view(VoiceAIPreviewView.post)
