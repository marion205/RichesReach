# Backend Server Connection - Verified ✅

## Server Status

### Health Check
The backend server is running and responding:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "schemaVersion": "1.0.0",
  "timestamp": "2025-11-07T18:02:30.232207"
}
```

### Server Details
- **URL**: `http://localhost:8000`
- **Status**: ✅ Running
- **Family Sharing API**: ✅ Registered and accessible

## Available Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /api/market/quotes` - Market data
- `POST /graphql/` - GraphQL endpoint

### Family Sharing Endpoints
- `GET /api/family/group` - Get family group
- `POST /api/family/group` - Create family group
- `POST /api/family/invite` - Invite member
- `POST /api/family/invite/accept` - Accept invite
- `PATCH /api/family/members/{id}/permissions` - Update permissions
- `POST /api/family/orb/sync` - Sync orb state
- `GET /api/family/orb/events` - Get sync events
- `DELETE /api/family/members/{id}` - Remove member
- `POST /api/family/group/leave` - Leave group

### Constellation AI Endpoints
- `POST /api/ai/life-events` - AI life event suggestions
- `POST /api/ai/growth-projections` - ML growth projections
- `POST /api/ai/shield-analysis` - AI market analysis
- `POST /api/ai/recommendations` - Personalized recommendations

## Mobile App Configuration

The mobile app is configured to connect to:
- **Development**: `http://localhost:8000` (iOS Simulator)
- **Physical Device**: Set `EXPO_PUBLIC_API_BASE_URL` to your Mac's LAN IP
  - Example: `http://192.168.1.100:8000`

### Check Current Configuration
The app uses `mobile/src/config/api.ts` which:
1. Checks `EXPO_PUBLIC_API_BASE_URL` environment variable
2. Falls back to `http://localhost:8000` for development
3. Logs the resolved API base URL at runtime

## Testing Connection from Mobile App

### From iOS Simulator
✅ Should work automatically with `localhost:8000`

### From Physical Device
1. Find your Mac's IP address:
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. Set environment variable:
   ```bash
   export EXPO_PUBLIC_API_BASE_URL=http://YOUR_IP:8000
   ```

3. Restart Expo/Metro bundler

## Connection Troubleshooting

### If you see timeout errors:

1. **Check server is running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check server logs**:
   ```bash
   tail -f /tmp/main_server.log
   ```

3. **Verify router registration**:
   Look for: `✅ Family Sharing API router registered`

4. **Check network connectivity**:
   - iOS Simulator: Should work with `localhost`
   - Physical device: Must use LAN IP, not `localhost`

### Common Issues

**Issue**: "Connection refused"
- **Solution**: Server not running. Start with `python3 main_server.py`

**Issue**: "Request timed out"
- **Solution**: Check firewall, verify IP address, ensure server is accessible

**Issue**: "404 Not Found"
- **Solution**: Router not registered. Check server logs for import errors

## Server Management

### Start Server
```bash
cd /Users/marioncollins/RichesReach
python3 main_server.py > /tmp/main_server.log 2>&1 &
```

### Stop Server
```bash
pkill -f main_server.py
```

### View Logs
```bash
tail -f /tmp/main_server.log
```

### Check Server Status
```bash
ps aux | grep main_server.py | grep -v grep
```

## Next Steps

The backend server is connected and ready! You can now:
1. ✅ Create family groups from the app
2. ✅ Invite family members
3. ✅ Sync orb state in real-time
4. ✅ Use all AI/ML features

Try accessing the family sharing feature from the Portfolio screen - it should work now!

