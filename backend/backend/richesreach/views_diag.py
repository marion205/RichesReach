from django.http import JsonResponse
import requests
import socket
import json

def echo(request):
    """Simple echo endpoint to test if app is responding"""
    return JsonResponse({"ok": True})

def netcheck(request):
    """Test outbound internet connectivity"""
    try:
        r = requests.get("https://api.ipify.org?format=json", timeout=5)
        return JsonResponse({"ok": True, "public_ip": r.json()["ip"]})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=502)
