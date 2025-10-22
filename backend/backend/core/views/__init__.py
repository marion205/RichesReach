# Views package
# Guard against missing mocks in prod
try:
    from .mock_tools import dev_sbloc_advance
except ImportError:
    def dev_sbloc_advance(request, advance_amount=None):
        from django.http import JsonResponse
        return JsonResponse({'error': 'Mock tools unavailable in this env'})

# Import AI views
try:
    from core.views_ai import ai_options_recommendations
except ImportError:
    def ai_options_recommendations(request):
        from django.http import JsonResponse
        return JsonResponse({'error': 'AI views unavailable in this env'})
