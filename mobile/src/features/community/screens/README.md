# Enhanced CircleDetailScreen Setup Guide

This guide explains how to set up the enhanced CircleDetailScreen with live streaming, viewer count tracking, and Stream.io chat integration.

## Features

- **Live Streaming**: Host live video streams using Agora SDK
- **Viewer Count**: Real-time viewer count tracking with Agora events
- **Stream.io Chat**: Real-time messaging overlay during live streams
- **Media Posts**: Image and video uploads with compression
- **Push Notifications**: Real-time notifications for new posts and live streams
- **Socket.io Integration**: Real-time updates for posts and comments

## Prerequisites

### 1. Agora Account Setup

1. Sign up at [Agora Console](https://console.agora.io/)
2. Create a new project
3. Get your App ID from the project dashboard
4. Enable video calling in your project settings

### 2. Stream.io Account Setup

1. Sign up at [GetStream.io](https://getstream.io/)
2. Create a new application
3. Get your API Key from the dashboard
4. Generate user tokens (server-side recommended for production)

### 3. Backend Endpoints

Ensure these endpoints are implemented in your Django backend:

- `GET /api/wealth-circles/` - List all wealth circles
- `GET /api/wealth-circles/{id}/posts/` - Get posts for a circle
- `POST /api/wealth-circles/{id}/posts/` - Create a new post
- `GET /api/posts/{id}/comments/` - Get comments for a post
- `POST /api/posts/{id}/comments/` - Create a new comment
- `POST /api/upload-media/` - Upload media files
- `POST /api/register-push-token/` - Register push notification token
- `POST /api/send-push-notification/` - Send push notifications
- `POST /api/agora-token/` - Generate Agora tokens
- `POST /api/live-stream-events/` - Handle live stream events
- `GET /api/video-compression-info/` - Get video compression settings

## Configuration

### 1. Environment Variables

Add these to your `mobile/env.local` file:

```bash
# Stream.io Configuration
EXPO_PUBLIC_STREAM_API_KEY=your_stream_api_key_here
EXPO_PUBLIC_STREAM_USER_TOKEN=your_stream_user_token_here

# Agora Configuration
EXPO_PUBLIC_AGORA_APP_ID=your_agora_app_id_here
EXPO_PUBLIC_AGORA_TOKEN=your_agora_token_here

# Backend API
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.236:8000
```

### 2. Update Configuration File

Edit `mobile/src/config/streamConfig.ts` and replace the placeholder values:

```typescript
export const STREAM_CONFIG = {
  API_KEY: 'your_actual_stream_api_key',
  USER_TOKEN: 'your_actual_stream_user_token',
  REGION: 'us-east-1',
};

export const AGORA_CONFIG = {
  APP_ID: 'your_actual_agora_app_id',
  TOKEN: null, // Optional for testing
};
```

## Installation

### 1. Install Dependencies

```bash
cd mobile
npm install stream-chat stream-chat-react-native react-native-agora
```

### 2. iOS Configuration

Add to `mobile/app.json`:

```json
{
  "expo": {
    "plugins": [
      [
        "expo-av",
        {
          "microphonePermission": "Allow $(PRODUCT_NAME) to access your microphone for live streaming."
        }
      ]
    ],
    "ios": {
      "infoPlist": {
        "NSMicrophoneUsageDescription": "This app needs access to microphone for live streaming.",
        "NSCameraUsageDescription": "This app needs access to camera for live streaming."
      }
    }
  }
}
```

### 3. Android Configuration

Add to `mobile/app.json`:

```json
{
  "expo": {
    "android": {
      "permissions": [
        "android.permission.RECORD_AUDIO",
        "android.permission.CAMERA",
        "android.permission.INTERNET",
        "android.permission.ACCESS_NETWORK_STATE"
      ]
    }
  }
}
```

## Usage

### 1. Basic Usage

```typescript
import CircleDetailScreenEnhanced from './CircleDetailScreenEnhanced';

// In your navigation
<CircleDetailScreenEnhanced 
  route={{ params: { circle: wealthCircle } }} 
  navigation={navigation} 
/>
```

### 2. Live Streaming Flow

1. **Host starts stream**: Tap "Go Live" button
2. **Viewers join**: Tap "Join Live" button when stream is active
3. **Real-time chat**: Use Stream.io chat overlay during live stream
4. **Viewer count**: Automatically tracked and displayed

### 3. Media Upload Flow

1. **Select media**: Tap camera button to pick image/video
2. **Compression**: Videos are automatically compressed
3. **Upload**: Media is uploaded to backend
4. **Post creation**: Post is created with media attachment

## Security Considerations

### 1. Token Generation

- **Stream.io tokens**: Generate server-side for production
- **Agora tokens**: Generate server-side for production
- **User authentication**: Implement proper user authentication

### 2. API Security

- **Rate limiting**: Implement rate limiting on backend endpoints
- **File validation**: Validate uploaded media files
- **User permissions**: Check user permissions for circle access

## Troubleshooting

### Common Issues

1. **Stream.io connection fails**
   - Check API key and user token
   - Verify network connectivity
   - Check Stream.io dashboard for errors

2. **Agora streaming issues**
   - Verify App ID is correct
   - Check microphone/camera permissions
   - Test with Agora's test tools

3. **Media upload fails**
   - Check file size limits
   - Verify backend endpoint is working
   - Check network connectivity

### Debug Mode

Enable debug logging by setting:

```typescript
// In streamConfig.ts
const isDevelopment = __DEV__;
console.log('Stream Config:', streamConfig);
console.log('Agora Config:', agoraConfig);
```

## Production Deployment

### 1. Server-side Token Generation

Implement these endpoints on your backend:

```python
# Generate Stream.io user token
def generate_stream_token(user_id):
    # Use Stream.io server SDK
    pass

# Generate Agora token
def generate_agora_token(channel_name, user_id):
    # Use Agora token builder
    pass
```

### 2. Environment Configuration

- Use production API keys
- Implement proper error handling
- Add monitoring and analytics
- Set up proper logging

### 3. Performance Optimization

- Implement video compression
- Add caching for media files
- Optimize real-time updates
- Monitor resource usage

## Support

For issues or questions:

1. Check the console logs for errors
2. Verify all configuration values
3. Test with minimal setup first
4. Check Agora and Stream.io documentation

## License

This implementation follows the same license as the main RichesReach project.
