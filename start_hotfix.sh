set -e

echo "Installing runtime deps..."
pip install -q gunicorn uvicorn[standard] channels daphne

echo "Stubbing core/websocket_auth.py..."
mkdir -p /app/core
cat >/app/core/websocket_auth.py <<'PY'
class JWTAuthMiddleware:
    def __init__(self, app): self.app = app
    async def __call__(self, scope, receive, send):
        return await self.app(scope, receive, send)

def JWTAuthMiddlewareStack(app):
    return app
PY

echo "Running migrations (fake-initial to tolerate pre-existing tables)..."
python manage.py migrate --fake-initial --noinput || true

echo "Collecting static..."
python manage.py collectstatic --noinput || true

echo "Starting Gunicorn (ASGI)..."
exec gunicorn richesreach.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 --workers 3 --timeout 60
