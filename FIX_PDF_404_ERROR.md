# Fix PDF Export 404 Error

## Issue
PDF export is returning 404: `{"detail":"Not Found"}`

## Root Cause
The backend server needs to be restarted to pick up the new `/api/tax/report/pdf` endpoint.

## Solution

### Step 1: Restart Backend Server

The endpoint is correctly defined in `deployment_package/backend/main.py` at line 218:
```python
@app.post("/api/tax/report/pdf")
async def generate_tax_report_pdf(request: Request):
```

But the server process (PID 30662) was started before this endpoint was added, so it needs a restart.

**To restart:**
1. Find the running process:
   ```bash
   ps aux | grep "python.*main.py" | grep -v grep
   ```

2. Kill the process:
   ```bash
   kill 30662
   # Or if that doesn't work:
   kill -9 30662
   ```

3. Restart the server:
   ```bash
   cd /Users/marioncollins/RichesReach/deployment_package/backend
   source ../../venv/bin/activate
   python main.py
   # Or use uvicorn:
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Step 2: Verify Endpoint is Available

After restarting, test the endpoint:
```bash
curl -X POST http://localhost:8000/api/tax/report/pdf \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"year": 2025, "filingStatus": "single", "state": "CA", "income": 80000}' \
  --output test.pdf
```

### Step 3: Check Server Logs

When you try to export PDF, check the backend logs for:
- Request received
- Any errors during PDF generation
- Response sent

## Verification

Once restarted, the endpoint should:
- ✅ Accept POST requests to `/api/tax/report/pdf`
- ✅ Return PDF content with `Content-Type: application/pdf`
- ✅ Include proper headers for file download

## Alternative: Check if Server is Running on Different Port

If the server is running on a different port, update `API_BASE` in `mobile/src/config/api.ts` to match.

## Quick Test

After restarting, try the PDF export again from the app. The error should be resolved.

