# core/views_gql_simple.py
import json
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from core.schema import schema

@method_decorator(csrf_exempt, name="dispatch")
class SimpleGraphQLView(View):
    def _execute(self, query, variables=None):
        result = schema.execute(query, variable_values=variables)
        payload = {}
        if result.errors:
            payload["errors"] = [str(e) for e in result.errors]
        if result.data is not None:
            payload["data"] = result.data
        return payload

    def get(self, request, *args, **kwargs):
        q = request.GET.get("query")
        if not q:
            return JsonResponse({"error":"missing query"}, status=400)
        return JsonResponse(self._execute(q))

    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body or "{}")
        except Exception:
            return JsonResponse({"error":"bad json"}, status=400)
        q = body.get("query")
        vars_ = body.get("variables")
        if not q:
            return JsonResponse({"error":"missing query"}, status=400)
        return JsonResponse(self._execute(q, vars_))
