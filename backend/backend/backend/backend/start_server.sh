#!/bin/bash

# Load environment variables
export DJANGO_DB_NAME=appdb
export DJANGO_DB_USER=appuser
export DJANGO_DB_PASSWORD=AppPass2025Simple
export DJANGO_DB_HOST=riches-reach-postgres.cmhsue8oy30k.us-east-1.rds.amazonaws.com
export DJANGO_DB_PORT=5432
export SSLMODE=require
export SECRET_KEY=django-insecure-production-key-change-in-production-1759071115
export DEBUG=True
export ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
export ALPHA_VANTAGE_API_KEY=K0A7XYLDNXHNQ1WI
export FINNHUB_API_KEY=d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0
export NEWS_API_KEY=94a335c7316145f79840edd62f77e11e
export REDIS_URL=redis://localhost:6379/0

# Activate virtual environment
source ../../../../.venv/bin/activate

# Start Django server
python manage.py runserver