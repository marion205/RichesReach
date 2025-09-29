# core/views_gql_simple.py
import json
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

print("DEBUG: Importing SimpleGraphQLView")
try:
    from core.schema_simple import schema
    print("DEBUG: Successfully imported simple schema")
except Exception as e:
    print(f"DEBUG: Error importing simple schema: {e}")
    # Fallback to original schema
    from core.schema import schema
    print("DEBUG: Using original schema as fallback")

@method_decorator(csrf_exempt, name="dispatch")
class SimpleGraphQLView(View):
    def _execute(self, query, variables=None):
        print(f"DEBUG: Executing query with simple schema: {query}")
        print(f"DEBUG: Schema type: {type(schema)}")
        result = schema.execute(query, variable_values=variables)
        print(f"DEBUG: Query result: {result}")
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
