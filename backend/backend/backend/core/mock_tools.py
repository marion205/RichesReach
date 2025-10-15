from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from core.models import SblocSession
from core.services.sbloc import SblocService

@require_POST
def dev_sbloc_advance(request, session_id: int):
    if not settings.DEBUG:
        return HttpResponseForbidden("DEBUG only")
    s = SblocSession.objects.get(pk=session_id)
    SblocService().advance_status(s)
    return JsonResponse({"ok": True, "new_status": s.status})
