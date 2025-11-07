# Server Start Instructions

## Issue
The backend server was not running, causing timeout errors when trying to access the Family Sharing API.

## Solution
The server has been started in the background. You should see it running now.

## Verify Server is Running

Check if the server is running:
```bash
ps aux | grep main_server.py | grep -v grep
```

Check server logs:
```bash
tail -f /tmp/main_server.log
```

## Test the Endpoint

Once the server is running, test the family sharing endpoint:
```bash
curl http://localhost:8000/api/family/group
```

You should see either:
- A 401 (authentication required) - this means the endpoint is working!
- A 404 (not found) - router not registered
- A 200 (success) - endpoint working with data

## If You Need to Restart the Server

1. Stop the current server:
   ```bash
   pkill -f main_server.py
   ```

2. Start it again:
   ```bash
   python3 main_server.py
   ```

   Or run in background:
   ```bash
   python3 main_server.py > /tmp/main_server.log 2>&1 &
   ```

## Check Router Registration

Look for this message in the server output:
```
✅ Family Sharing API router registered
```

If you see:
```
⚠️ Family Sharing API router not available: [error]
```

Then there's still an import issue that needs to be fixed.

