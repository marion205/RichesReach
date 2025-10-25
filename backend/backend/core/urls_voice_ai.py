"""
Voice AI URL patterns for RichesReach
"""

from django.urls import path
from . import views_voice_ai

urlpatterns = [
    # Main TTS synthesis endpoint
    path('synthesize/', views_voice_ai.VoiceAIView.as_view(), name='voice_ai_synthesize'),
    
    # Audio file serving
    path('audio/<str:filename>/', views_voice_ai.VoiceAIAudioView.as_view(), name='voice_ai_audio'),
    
    # Available voices
    path('voices/', views_voice_ai.VoiceAIVoicesView.as_view(), name='voice_ai_voices'),
    
    # Health check
    path('health/', views_voice_ai.VoiceAIHealthView.as_view(), name='voice_ai_health'),
]
