"""
SBLOC Webhook Views
Handle webhooks from SBLOC aggregator
"""
import json
import hmac
import hashlib
import logging
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from .models import SblocReferral

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def sbloc_webhook(request):
    """Handle webhooks from SBLOC aggregator"""
    raw = request.body
    sig = request.headers.get("X-Webhook-Signature", "")
    expected = hmac.new(settings.SBLOC_WEBHOOK_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return HttpResponse(status=401)

    evt = json.loads(raw)
    app_id, vendor_status = evt["applicationId"], evt["status"]
    status_map = {
        "created": "DRAFT",
        "submitted": "SUBMITTED", 
        "in_review": "IN_REVIEW",
        "conditional_approval": "CONDITIONAL_APPROVAL",
        "approved": "APPROVED",
        "declined": "DECLINED",
        "withdrawn": "WITHDRAWN",
        "funded": "FUNDED",
    }
    ref = SblocReferral.objects.filter(external_ref=app_id).first()
    if ref:
        ref.status = status_map.get(vendor_status, ref.status)
        ref.save(update_fields=["status"])
    return JsonResponse({"ok": True})


def _verify_webhook_signature(request):
    """
    Verify webhook signature using HMAC
    """
    if not settings.SBLOC_WEBHOOK_SECRET:
        logger.warning("No webhook secret configured")
        return False
    
    signature = request.headers.get("X-Webhook-Signature", "")
    if not signature:
        logger.warning("No webhook signature provided")
        return False
    
    # Calculate expected signature
    expected_signature = hmac.new(
        settings.SBLOC_WEBHOOK_SECRET.encode(),
        request.body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(signature, expected_signature)


@csrf_exempt
@require_http_methods(["GET"])
def sbloc_callback(request):
    """
    Handle callback from SBLOC aggregator after application completion
    """
    try:
        # Extract callback parameters
        application_id = request.GET.get("applicationId")
        status = request.GET.get("status")
        success = request.GET.get("success", "false").lower() == "true"
        
        logger.info(f"SBLOC callback received: {application_id}, status: {status}, success: {success}")
        
        if application_id:
            # Find referral and update status
            try:
                referral = SBLOCReferral.objects.get(aggregator_app_id=application_id)
                processor = SBLOCDataProcessor()
                
                if success:
                    mapped_status = processor.aggregator_service._map_aggregator_status(status or "submitted")
                else:
                    mapped_status = "WITHDRAWN"
                
                processor.update_referral_status(
                    referral=referral,
                    new_status=mapped_status,
                    note=f"Application completed via callback",
                    source="callback"
                )
                
                logger.info(f"Updated referral {referral.id} via callback")
                
            except SBLOCReferral.DoesNotExist:
                logger.error(f"Referral not found for callback: {application_id}")
        
        # Return success response (this will be displayed to user)
        return HttpResponse("""
        <html>
        <head><title>SBLOC Application</title></head>
        <body>
            <h1>Application Submitted</h1>
            <p>Your SBLOC application has been submitted successfully.</p>
            <p>You can close this window and return to the app.</p>
        </body>
        </html>
        """, content_type="text/html")
        
    except Exception as e:
        logger.error(f"Callback processing error: {e}")
        return HttpResponse("""
        <html>
        <head><title>Error</title></head>
        <body>
            <h1>Error</h1>
            <p>There was an error processing your application.</p>
            <p>Please contact support if this issue persists.</p>
        </body>
        </html>
        """, content_type="text/html", status=500)


@require_http_methods(["GET"])
def sbloc_health(request):
    """
    Health check endpoint for SBLOC webhooks
    """
    return JsonResponse({
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
        "webhook_secret_configured": bool(settings.SBLOC_WEBHOOK_SECRET),
        "aggregator_enabled": settings.USE_SBLOC_AGGREGATOR
    })
