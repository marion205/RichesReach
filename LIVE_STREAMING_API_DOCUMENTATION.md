# 🎥 RichesReach Live Streaming API Documentation

## Overview
The RichesReach Live Streaming API provides comprehensive endpoints for managing live streams, polls, Q&A sessions, and screen sharing within wealth circles.

## Base URL
```
http://192.168.1.236:8000/api/
```

## Authentication
All endpoints require authentication. Include the user token in the request headers:
```
Authorization: Bearer <token>
```

---

## 📺 Live Streams

### List Live Streams
**GET** `/live-streams/`

**Query Parameters:**
- `circle_id` (optional): Filter by wealth circle ID
- `category` (optional): Filter by stream category
- `status` (optional): Filter by stream status (default: 'live')
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "title": "Market Analysis Live",
      "description": "Daily market insights",
      "category": "market-analysis",
      "status": "live",
      "host": {
        "id": 1,
        "username": "trader_john",
        "first_name": "John",
        "last_name": "Doe"
      },
      "circle": {
        "id": 1,
        "name": "BIPOC Wealth Builders"
      },
      "viewer_count": 45,
      "max_viewers": 67,
      "total_reactions": 123,
      "total_messages": 89,
      "started_at": "2024-01-15T10:30:00Z",
      "duration": "00:45:30",
      "is_public": true,
      "allow_chat": true,
      "allow_reactions": true,
      "allow_screen_share": false,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "total_pages": 3,
    "total_count": 45,
    "has_next": true,
    "has_previous": false
  }
}
```

### Create Live Stream
**POST** `/live-streams/`

**Request Body:**
```json
{
  "title": "Portfolio Review Session",
  "description": "Monthly portfolio review and Q&A",
  "circle_id": 1,
  "category": "portfolio-review",
  "is_public": true,
  "allow_chat": true,
  "allow_reactions": true,
  "allow_screen_share": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Portfolio Review Session",
    "description": "Monthly portfolio review and Q&A",
    "category": "portfolio-review",
    "status": "scheduled",
    "stream_key": "stream_abc123",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### Get Stream Details
**GET** `/live-streams/{stream_id}/`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Market Analysis Live",
    "description": "Daily market insights",
    "category": "market-analysis",
    "status": "live",
    "host": {
      "id": 1,
      "username": "trader_john",
      "first_name": "John",
      "last_name": "Doe"
    },
    "circle": {
      "id": 1,
      "name": "BIPOC Wealth Builders"
    },
    "viewer_count": 45,
    "max_viewers": 67,
    "total_reactions": 123,
    "total_messages": 89,
    "started_at": "2024-01-15T10:30:00Z",
    "ended_at": null,
    "duration": "00:45:30",
    "is_public": true,
    "allow_chat": true,
    "allow_reactions": true,
    "allow_screen_share": false,
    "stream_urls": {
      "rtmp": "rtmp://your-streaming-server.com/live/stream_abc123",
      "hls": "https://your-cdn.com/hls/stream_abc123.m3u8",
      "webrtc": "wss://your-signaling-server.com/stream/stream_abc123"
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### Start Stream
**POST** `/live-streams/{stream_id}/start/`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "live",
    "started_at": "2024-01-15T10:30:00Z",
    "stream_key": "stream_abc123",
    "stream_urls": {
      "rtmp": "rtmp://your-streaming-server.com/live/stream_abc123",
      "hls": "https://your-cdn.com/hls/stream_abc123.m3u8",
      "webrtc": "wss://your-signaling-server.com/stream/stream_abc123"
    }
  }
}
```

### End Stream
**POST** `/live-streams/{stream_id}/end/`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "status": "ended",
    "ended_at": "2024-01-15T11:15:00Z",
    "duration": "00:45:00"
  }
}
```

---

## 👥 Stream Viewers

### Join Stream
**POST** `/live-streams/{stream_id}/join/`

**Response:**
```json
{
  "success": true,
  "data": {
    "viewer_id": "uuid",
    "stream_id": "uuid",
    "joined_at": "2024-01-15T10:30:00Z",
    "viewer_count": 46
  }
}
```

### Leave Stream
**POST** `/live-streams/{stream_id}/leave/`

**Response:**
```json
{
  "success": true,
  "data": {
    "viewer_id": "uuid",
    "stream_id": "uuid",
    "left_at": "2024-01-15T11:00:00Z",
    "watch_time": "00:30:00"
  }
}
```

### Get Stream Viewers
**GET** `/live-streams/{stream_id}/viewers/`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 50)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "user": {
        "id": 2,
        "username": "investor_jane",
        "first_name": "Jane",
        "last_name": "Smith"
      },
      "joined_at": "2024-01-15T10:30:00Z",
      "reactions_sent": 5,
      "messages_sent": 12
    }
  ],
  "pagination": {
    "page": 1,
    "total_pages": 2,
    "total_count": 67,
    "has_next": true,
    "has_previous": false
  }
}
```

---

## 💬 Stream Messages

### Get Stream Messages
**GET** `/live-streams/{stream_id}/messages/`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 50)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "user": {
        "id": 2,
        "username": "investor_jane",
        "first_name": "Jane",
        "last_name": "Smith"
      },
      "message_type": "message",
      "content": "Great insights on the market today!",
      "is_pinned": false,
      "likes": 3,
      "replies": 1,
      "created_at": "2024-01-15T10:35:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "total_pages": 5,
    "total_count": 89,
    "has_next": true,
    "has_previous": false
  }
}
```

### Send Message
**POST** `/live-streams/{stream_id}/messages/send/`

**Request Body:**
```json
{
  "content": "What do you think about the current market volatility?",
  "message_type": "message"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "user": {
      "id": 2,
      "username": "investor_jane",
      "first_name": "Jane",
      "last_name": "Smith"
    },
    "message_type": "message",
    "content": "What do you think about the current market volatility?",
    "created_at": "2024-01-15T10:35:00Z"
  }
}
```

---

## 🎭 Stream Reactions

### Send Reaction
**POST** `/live-streams/{stream_id}/reactions/send/`

**Request Body:**
```json
{
  "reaction_type": "fire"
}
```

**Available Reaction Types:**
- `heart` - ❤️ Heart
- `fire` - 🔥 Fire
- `money` - 💰 Money
- `thumbs` - 👍 Thumbs Up
- `clap` - 👏 Clap
- `laugh` - 😂 Laugh

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "reaction_type": "fire",
    "user": {
      "id": 2,
      "username": "investor_jane"
    },
    "created_at": "2024-01-15T10:35:00Z"
  }
}
```

### Get Recent Reactions
**GET** `/live-streams/{stream_id}/reactions/`

**Query Parameters:**
- `limit` (optional): Number of reactions to return (default: 100)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "reaction_type": "fire",
      "user": {
        "id": 2,
        "username": "investor_jane"
      },
      "created_at": "2024-01-15T10:35:00Z"
    }
  ]
}
```

---

## 📊 Stream Polls

### Create Poll
**POST** `/live-streams/{stream_id}/polls/create/`

**Request Body:**
```json
{
  "question": "What's your biggest investment challenge?",
  "options": [
    "Market volatility",
    "Lack of knowledge",
    "Emotional decisions",
    "Time management"
  ],
  "is_multiple_choice": false,
  "expires_in": 10
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "question": "What's your biggest investment challenge?",
    "is_multiple_choice": false,
    "is_active": true,
    "expires_at": "2024-01-15T10:40:00Z",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### Get Active Polls
**GET** `/live-streams/{stream_id}/polls/`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "question": "What's your biggest investment challenge?",
      "is_multiple_choice": false,
      "is_active": true,
      "total_votes": 23,
      "expires_at": "2024-01-15T10:40:00Z",
      "created_at": "2024-01-15T10:30:00Z",
      "options": [
        {
          "id": "uuid",
          "text": "Market volatility",
          "votes": 8,
          "order": 0
        },
        {
          "id": "uuid",
          "text": "Lack of knowledge",
          "votes": 7,
          "order": 1
        },
        {
          "id": "uuid",
          "text": "Emotional decisions",
          "votes": 5,
          "order": 2
        },
        {
          "id": "uuid",
          "text": "Time management",
          "votes": 3,
          "order": 3
        }
      ]
    }
  ]
}
```

### Vote on Poll
**POST** `/live-streams/{stream_id}/polls/{poll_id}/vote/`

**Request Body:**
```json
{
  "option_ids": ["uuid"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "poll_id": "uuid",
    "votes_cast": 1,
    "total_votes": 24
  }
}
```

---

## ❓ Q&A Sessions

### Start Q&A Session
**POST** `/live-streams/{stream_id}/qa/start/`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "stream_id": "uuid",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### Submit Question
**POST** `/live-streams/{stream_id}/qa/questions/submit/`

**Request Body:**
```json
{
  "question": "How do you handle market downturns in your portfolio?"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "question": "How do you handle market downturns in your portfolio?",
    "status": "pending",
    "upvotes": 0,
    "created_at": "2024-01-15T10:35:00Z"
  }
}
```

### Get Questions
**GET** `/live-streams/{stream_id}/qa/questions/`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "user": {
        "id": 2,
        "username": "investor_jane",
        "first_name": "Jane",
        "last_name": "Smith"
      },
      "question": "How do you handle market downturns in your portfolio?",
      "status": "answered",
      "answer": "I maintain a diversified portfolio and use dollar-cost averaging...",
      "answered_by": {
        "id": 1,
        "username": "trader_john"
      },
      "answered_at": "2024-01-15T10:40:00Z",
      "upvotes": 5,
      "created_at": "2024-01-15T10:35:00Z"
    }
  ]
}
```

---

## 🖥️ Screen Sharing

### Start Screen Share
**POST** `/live-streams/{stream_id}/screen-share/start/`

**Request Body:**
```json
{
  "share_type": "screen",
  "title": "Portfolio Analysis Dashboard"
}
```

**Share Types:**
- `screen` - Full screen
- `window` - Specific window
- `tab` - Browser tab

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "share_type": "screen",
    "title": "Portfolio Analysis Dashboard",
    "is_active": true,
    "started_at": "2024-01-15T10:30:00Z"
  }
}
```

### Stop Screen Share
**POST** `/live-streams/{stream_id}/screen-share/stop/`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "is_active": false,
    "ended_at": "2024-01-15T11:00:00Z"
  }
}
```

---

## 🚨 Error Responses

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

## 📱 Mobile Integration

### React Native Implementation
The mobile app uses the `AdvancedLiveStreaming` component which integrates with these APIs:

```typescript
// Example usage in React Native
const createStream = async () => {
  const response = await fetch('http://192.168.1.236:8000/api/live-streams/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      title: 'Market Analysis Live',
      circle_id: circleId,
      category: 'market-analysis',
    }),
  });
  
  const data = await response.json();
  return data;
};
```

### WebSocket Integration
For real-time features, the API supports WebSocket connections for:
- Live viewer count updates
- Real-time chat messages
- Live reactions
- Poll results
- Q&A questions

---

## 🔧 Development Setup

### Django Backend
1. Add the live streaming models to your Django project
2. Run migrations: `python manage.py migrate`
3. Include the URL patterns in your main `urls.py`
4. Start the development server: `python manage.py runserver 192.168.1.236:8000`

### Mobile App
1. Install required dependencies:
   ```bash
   npm install react-native-webrtc socket.io-client
   ```
2. Update your API base URL to point to the Django backend
3. Test the live streaming features

---

## 🎯 Next Steps

1. **Set up streaming infrastructure** (RTMP server, CDN)
2. **Implement WebSocket real-time updates**
3. **Add push notifications for stream events**
4. **Integrate with existing wealth circle features**
5. **Add analytics and reporting**
6. **Implement content moderation**
7. **Add stream recording and playback**

---

## 📞 Support

For technical support or questions about the Live Streaming API, please contact the RichesReach development team.
