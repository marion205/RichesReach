"""
API Views for Wake Word Model Serving
Serves model files and normalization parameters
"""

from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from pathlib import Path
import json
import os

# Model directory: backend/backend/ml_models/wake_word
MODEL_DIR = Path(__file__).parent.parent / 'ml_models' / 'wake_word'


@csrf_exempt
def serve_normalization_params(request):
    """Serve normalization parameters for wake word model"""
    try:
        norm_file = MODEL_DIR / 'normalization.json'
        
        if not norm_file.exists():
            return JsonResponse({
                'error': 'Normalization parameters not found. Train the model first.'
            }, status=404)
        
        with open(norm_file, 'r') as f:
            params = json.load(f)
        
        return JsonResponse(params)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def serve_model_info(request):
    """Serve model metadata"""
    try:
        model_file = MODEL_DIR / 'wake_word_model.tflite'
        tfjs_dir = MODEL_DIR / 'tfjs_model'
        
        info = {
            'tflite_available': model_file.exists(),
            'tfjs_available': tfjs_dir.exists(),
            'model_path': str(model_file) if model_file.exists() else None,
            'tfjs_path': str(tfjs_dir) if tfjs_dir.exists() else None,
        }
        
        return JsonResponse(info)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

