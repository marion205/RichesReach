# Backend Server Setup Instructions

## Issue
The backend server cannot start because required Python packages are missing.

## Required Packages
The server needs these packages installed:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `graphql_jwt` (optional) - JWT authentication (we have fallback)

## Installation

### Option 1: Install in User Directory (Recommended)
```bash
python3 -m pip install fastapi uvicorn --user
```

### Option 2: Use Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install packages
pip install fastapi uvicorn
```

### Option 3: Install System-Wide (Requires sudo)
```bash
sudo pip3 install fastapi uvicorn
```

## Start the Server

Once packages are installed:

```bash
cd /Users/marioncollins/RichesReach
python3 main_server.py
```

Or run in background:
```bash
python3 main_server.py > /tmp/main_server.log 2>&1 &
```

## Verify Server is Running

1. Check if server started:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check for router registration:
   ```bash
   tail -f /tmp/main_server.log | grep "Family Sharing"
   ```

   You should see:
   ```
   ✅ Family Sharing API router registered
   ```

3. Test the endpoint:
   ```bash
   curl http://localhost:8000/api/family/group
   ```

## Troubleshooting

### If you see "ModuleNotFoundError"
- Make sure you're using the same Python interpreter that has the packages installed
- Check: `python3 -c "import fastapi; print(fastapi.__version__)"`

### If router still doesn't register
- Check the server logs for import errors
- Verify the file path: `deployment_package/backend/core/family_sharing_api.py` exists
- Make sure Django is properly configured

### If endpoints return 404
- Verify router registration message appears in logs
- Check that the router prefix matches: `/api/family`
- Restart the server after making code changes

