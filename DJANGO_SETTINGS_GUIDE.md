# Django Settings Configuration Guide

## 📁 Location

**Settings File**: `deployment_package/backend/richesreach/settings.py`

**Full Path**: `/Users/marioncollins/RichesReach/deployment_package/backend/richesreach/settings.py`

**Settings Module**: `richesreach.settings`

## 🔍 How to Find It

```bash
# From project root
cd deployment_package/backend/richesreach
ls -la settings.py

# Or find it
find . -name "settings.py" -type f
```

## 📝 Settings File Structure

The settings file contains:
- **INSTALLED_APPS**: Django apps including `core` (your banking app)
- **DATABASES**: Database configuration
- **CACHES**: Redis caching configuration
- **GRAPHENE**: GraphQL schema configuration
- **CELERY**: Task queue configuration
- **Yodlee settings**: (if configured via environment variables)

## ✅ What Was Fixed

1. ✅ **Syntax Error**: Fixed indentation on line 144
2. ✅ **Path Detection**: Updated `main_server.py` to find `deployment_package/backend`
3. ✅ **Settings Module**: Configured to use `richesreach.settings`

## 🔧 Current Status

- **Settings file**: Found and fixed ✅
- **Django path**: Configured correctly ✅
- **Apps loading**: May need Django initialization check ⚠️

## 💡 To Edit Settings

Simply open the file:
```bash
code deployment_package/backend/richesreach/settings.py
# or
vim deployment_package/backend/richesreach/settings.py
```

The settings file is a standard Django settings file and can be edited like any Python file.
