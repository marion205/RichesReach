FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps (adjust for your stack)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first for better caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app AFTER deps so caches work
COPY . /app

# Optional: verify the exact file made it into the image (helps catch "stale file")
RUN python - <<'PY'
from pathlib import Path
p = Path("core/consumers.py")
print(">>> consumers.py exists:", p.exists())
if p.exists():
    lines = p.read_text().splitlines()[:2]
    print(">>> First 2 lines:")
    for i, line in enumerate(lines, 1):
        print(f"  {i}: {line}")
else:
    print(">>> ERROR: consumers.py not found!")
PY

# Create non-root user
RUN useradd -m appuser
USER appuser

# Entrypoint runs migrations then serves
COPY docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
EXPOSE 8000
