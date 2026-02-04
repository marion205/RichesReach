"""
REST API Views for Voice/TTS Services
"""
import json
import os
import logging

from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)

# Polly output format to content-type
POLLY_FORMAT_TO_CONTENT_TYPE = {
    "mp3": "audio/mpeg",
    "ogg_vorbis": "audio/ogg",
    "ogg": "audio/ogg",
}


# CSRF exempt - Bearer token auth only (see CSRF_VERIFICATION_CHECKLIST.md)
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


@method_decorator(csrf_exempt, name='dispatch')
class PollySynthesizeView(View):
    """
    POST /polly/synthesize
    Body: { "text": "...", "voiceId": "Joanna", "format": "mp3" }
    Returns: binary audio (e.g. audio/mpeg for mp3).
    Used by mobile TTS client when provider is 'polly'.
    """
    def post(self, request):
        try:
            body = json.loads(request.body or "{}")
            text = (body.get("text") or "").strip()
            voice_id = (body.get("voiceId") or "Joanna").strip()
            fmt = (body.get("format") or "mp3").strip().lower()
            if fmt not in POLLY_FORMAT_TO_CONTENT_TYPE:
                fmt = "mp3"
            output_format = "ogg_vorbis" if fmt == "ogg" else fmt
            if not text:
                return JsonResponse({"error": "Missing or empty 'text'"}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({"error": f"Invalid JSON: {e}"}, status=400)

        try:
            import boto3
            region = os.getenv("AWS_REGION", "us-east-1")
            client = boto3.client("polly", region_name=region)
            response = client.synthesize_speech(
                Text=text,
                OutputFormat=output_format,
                VoiceId=voice_id,
            )
            audio_bytes = response["AudioStream"].read()
            content_type = POLLY_FORMAT_TO_CONTENT_TYPE.get(fmt, "audio/mpeg")
            return HttpResponse(audio_bytes, content_type=content_type)
        except ImportError:
            logger.warning("boto3 not installed - Polly TTS unavailable")
            return JsonResponse(
                {"error": "TTS not configured (boto3 required for Polly)"},
                status=503,
            )
        except Exception as e:
            logger.exception("Polly synthesize_speech failed")
            return JsonResponse(
                {"error": str(e)},
                status=503,
            )


@method_decorator(csrf_exempt, name='dispatch')
class VoicePreviewView(View):
    """
    POST /api/preview/ or /api/preview
    Body: { "text"|"sample": "...", "voiceId"|"voice": "Joanna", "format": "mp3" }
    Returns: { "success": true, "audio_url": "data:audio/mpeg;base64,..." }
    Used by mobile VoiceAI component for voice preview button.
    """
    def post(self, request):
        try:
            body = json.loads(request.body or "{}")
            text = (body.get("text") or body.get("sample") or "This is a quick voice preview.").strip()
            voice_id = (body.get("voiceId") or body.get("voice") or "Joanna").strip()
            fmt = (body.get("format") or "mp3").strip().lower()
            output_format = "ogg_vorbis" if fmt == "ogg" else "mp3"
        except json.JSONDecodeError as e:
            return JsonResponse({"success": False, "error": f"Invalid JSON: {e}"}, status=400)

        try:
            import boto3
            import base64
            region = os.getenv("AWS_REGION", "us-east-1")
            client = boto3.client("polly", region_name=region)
            response = client.synthesize_speech(
                Text=text,
                OutputFormat=output_format,
                VoiceId=voice_id,
            )
            audio_bytes = response["AudioStream"].read()
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            content_type = "audio/ogg" if fmt == "ogg" else "audio/mpeg"
            return JsonResponse({
                "success": True,
                "audio_url": f"data:{content_type};base64,{audio_b64}",
                "format": fmt,
            })
        except ImportError:
            return JsonResponse(
                {"success": False, "error": "TTS not configured (boto3 required)"},
                status=503,
            )
        except Exception as e:
            logger.exception("Voice preview failed")
            return JsonResponse(
                {"success": False, "error": str(e)},
                status=503,
            )

