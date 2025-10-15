# AI Options Debugging Guide

## Current Status

### ✅ Server is Working
- Server is running on `http://192.168.1.151:8000`
- AI Options endpoint is working: `/api/ai-options/recommendations`
- Server returns valid JSON responses with 200 status codes
- Tested with curl - returns proper recommendations

### ❌ Mobile App is Failing
- Getting "Failed to generate recommendations" error when clicking regenerate
- Error is coming from `AIOptionsScreen.tsx` line 80

## What to Check in Mobile App

### 1. Check Expo Logs
Open the Expo console and look for these debug messages we added:

```
Response status: 200
Response headers: [Headers object]
Content-Type: application/json
Raw response text (first 200 chars): {"symbol": "AAPL", ...
```

If you see these logs, the request is reaching the server successfully.

### 2. Check for Error Messages
Look for these error messages in the Expo console:

```
❌ Error getting AI options recommendations: [Error]
❌ Error details: { name, message, stack }
❌ JSON Parse error: ...
❌ HTTP Error Response: ...
```

These will tell us exactly what's failing.

### 3. Check Network Configuration
In the Expo console, look for this log message:

```
🔧 API Configuration: { API_HTTP, API_GRAPHQL, API_AUTH, API_WS }
```

Make sure `API_HTTP` is set to `http://192.168.1.151:8000`

### 4. Check if App is Using Updated Code
Make sure your Expo app has reloaded with the new debugging code:
- Shake the device/simulator
- Tap "Reload" in the Expo menu
- Or run `expo start --clear` to clear cache

### 5. Test the Endpoint Directly
From your mobile device/simulator, try accessing:
```
http://192.168.1.151:8000/api/ai-options/recommendations
```

If this doesn't work, there might be a network connectivity issue.

## Common Issues

### Issue: Network Connectivity
- Make sure your mobile device/simulator is on the same network as your Mac
- Try pinging `192.168.1.151` from your mobile device
- Check firewall settings on your Mac

### Issue: Port Confusion
- Make sure the app is not trying to hit port 8081 (Expo Metro bundler)
- The API should be on port 8000

### Issue: Environment Variables Not Loaded
- Environment variables only reload when Expo restarts
- Run `expo start --clear` to reload environment variables
- Check `.env.local` exists and has correct values

### Issue: CORS Errors
- Check the Expo console for CORS errors
- Server has CORS enabled for all origins (dev only)

### Issue: Invalid JSON Response
- Check if the response is HTML instead of JSON
- Look for "Unexpected character" errors in the logs
- This usually means Django is returning an error page instead of JSON

## Quick Test
Run this from terminal to verify server is working:

```bash
curl -X POST http://192.168.1.151:8000/api/ai-options/recommendations \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","portfolio_value":10000,"time_horizon":30,"user_risk_tolerance":"medium"}' \
  | jq '.recommendations[0].strategy_name'
```

Should return: `"Iron Condor"` or similar strategy name

## Next Steps
1. Check the Expo console logs for debugging output
2. Share the error messages you see in the logs
3. Try reloading the Expo app to ensure it has the latest code
4. Verify network connectivity from your mobile device to the server
