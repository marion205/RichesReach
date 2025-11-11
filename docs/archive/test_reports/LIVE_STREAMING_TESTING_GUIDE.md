# 🧪 RichesReach Live Streaming Testing Guide

## Overview
This guide provides comprehensive testing procedures for the RichesReach Live Streaming feature, covering both manual and automated testing scenarios.

## 🎯 Testing Objectives

### Primary Goals
- ✅ Verify live streaming functionality works end-to-end
- ✅ Ensure real-time features (chat, reactions, polls) work correctly
- ✅ Test screen sharing capabilities
- ✅ Validate Q&A session management
- ✅ Confirm proper error handling and edge cases
- ✅ Test performance with multiple concurrent users

### Success Criteria
- Hosts can successfully start and end live streams
- Viewers can join streams and interact in real-time
- All real-time features work without significant delays
- System handles network interruptions gracefully
- Performance remains stable with 50+ concurrent viewers

---

## 🧪 Manual Testing Scenarios

### 1. Basic Live Streaming Flow

#### Test Case 1.1: Host Starts Stream
**Objective:** Verify a host can successfully start a live stream

**Steps:**
1. Open the RichesReach mobile app
2. Navigate to a wealth circle
3. Tap "Go Live" button
4. Fill in stream details:
   - Title: "Market Analysis Live"
   - Category: "Market Analysis"
   - Description: "Daily market insights and analysis"
5. Tap "Start Stream"
6. Grant camera and microphone permissions
7. Verify stream starts successfully

**Expected Results:**
- ✅ Stream starts with live indicator
- ✅ Host video feed displays correctly
- ✅ Stream info header shows correct details
- ✅ Duration timer starts counting
- ✅ Stream appears in live streams list

**Test Data:**
```json
{
  "title": "Market Analysis Live",
  "category": "market-analysis",
  "description": "Daily market insights and analysis",
  "circle_id": 1
}
```

#### Test Case 1.2: Viewer Joins Stream
**Objective:** Verify a viewer can join an active live stream

**Steps:**
1. Open the RichesReach mobile app on a different device
2. Navigate to the same wealth circle
3. Tap "Join Live" button
4. Verify viewer joins successfully

**Expected Results:**
- ✅ Viewer count increases by 1
- ✅ Host video feed displays for viewer
- ✅ Chat interface is available
- ✅ Reaction buttons are functional
- ✅ Viewer can see stream info

#### Test Case 1.3: Host Ends Stream
**Objective:** Verify a host can properly end a live stream

**Steps:**
1. From the host's device, tap "End Stream"
2. Confirm the action
3. Verify stream ends

**Expected Results:**
- ✅ Stream status changes to "ended"
- ✅ All viewers are disconnected
- ✅ Stream duration is recorded
- ✅ Stream appears in ended streams list

### 2. Real-Time Chat Testing

#### Test Case 2.1: Send Chat Messages
**Objective:** Verify chat messages are sent and received in real-time

**Steps:**
1. Start a live stream as host
2. Join the stream as a viewer
3. Send a message from viewer: "Great insights!"
4. Verify message appears for both host and viewer
5. Send a reply from host: "Thank you!"

**Expected Results:**
- ✅ Messages appear instantly for all participants
- ✅ Message formatting is correct
- ✅ User information displays properly
- ✅ Message timestamps are accurate

**Test Messages:**
```
Viewer: "Great insights on the market today!"
Host: "Thank you! Any questions?"
Viewer: "What's your take on crypto volatility?"
Host: "I'll cover that in the next segment"
```

#### Test Case 2.2: Chat Moderation
**Objective:** Verify chat moderation features work correctly

**Steps:**
1. Start a live stream as host
2. Join as a viewer
3. Send inappropriate message: "This is spam"
4. As host, try to moderate the message
5. Verify moderation actions work

**Expected Results:**
- ✅ Host can delete inappropriate messages
- ✅ Host can mute problematic users
- ✅ Moderation actions are applied immediately

### 3. Live Reactions Testing

#### Test Case 3.1: Send Reactions
**Objective:** Verify live reactions work correctly

**Steps:**
1. Start a live stream as host
2. Join as a viewer
3. Tap reaction buttons: ❤️, 🔥, 💰, 👍
4. Verify reactions appear on screen
5. Check reaction count updates

**Expected Results:**
- ✅ Reactions appear as animated emojis
- ✅ Reactions float up the screen
- ✅ Reaction count increases
- ✅ Reactions disappear after 3 seconds

**Test Reactions:**
- Heart (❤️) - 5 times
- Fire (🔥) - 3 times
- Money (💰) - 2 times
- Thumbs Up (👍) - 4 times

#### Test Case 3.2: Reaction Spam Handling
**Objective:** Verify system handles reaction spam gracefully

**Steps:**
1. Start a live stream as host
2. Join as a viewer
3. Rapidly tap reaction buttons 20 times
4. Verify system handles the spam

**Expected Results:**
- ✅ System limits reaction frequency
- ✅ No performance degradation
- ✅ UI remains responsive

### 4. Polls Testing

#### Test Case 4.1: Create and Vote on Poll
**Objective:** Verify poll creation and voting functionality

**Steps:**
1. Start a live stream as host
2. Create a poll:
   - Question: "What's your biggest investment challenge?"
   - Options: ["Market volatility", "Lack of knowledge", "Emotional decisions"]
3. Join as a viewer
4. Vote on the poll
5. Verify results update in real-time

**Expected Results:**
- ✅ Poll appears for all viewers
- ✅ Voting is instant
- ✅ Results update in real-time
- ✅ Poll expires after specified time

**Test Poll Data:**
```json
{
  "question": "What's your biggest investment challenge?",
  "options": [
    "Market volatility",
    "Lack of knowledge", 
    "Emotional decisions",
    "Time management"
  ],
  "expires_in": 10
}
```

#### Test Case 4.2: Multiple Choice Poll
**Objective:** Verify multiple choice polls work correctly

**Steps:**
1. Start a live stream as host
2. Create a multiple choice poll
3. Join as a viewer
4. Select multiple options
5. Verify results display correctly

**Expected Results:**
- ✅ Multiple options can be selected
- ✅ Results show percentage for each option
- ✅ Total votes are accurate

### 5. Q&A Session Testing

#### Test Case 5.1: Submit and Answer Questions
**Objective:** Verify Q&A session functionality

**Steps:**
1. Start a live stream as host
2. Start Q&A session
3. Join as a viewer
4. Submit question: "How do you handle market downturns?"
5. As host, answer the question
6. Verify Q&A flow works correctly

**Expected Results:**
- ✅ Questions appear in host's Q&A queue
- ✅ Host can answer questions
- ✅ Answers are visible to all viewers
- ✅ Q&A session can be ended

**Test Questions:**
```
Q1: "How do you handle market downturns?"
Q2: "What's your favorite investment strategy?"
Q3: "How often do you rebalance your portfolio?"
```

#### Test Case 5.2: Question Upvoting
**Objective:** Verify question upvoting system

**Steps:**
1. Start a live stream as host
2. Start Q&A session
3. Join as multiple viewers
4. Submit questions
5. Upvote popular questions
6. Verify upvoting works

**Expected Results:**
- ✅ Questions can be upvoted
- ✅ Popular questions rise to the top
- ✅ Upvote counts are accurate

### 6. Screen Sharing Testing

#### Test Case 6.1: Host Screen Share
**Objective:** Verify host can share their screen

**Steps:**
1. Start a live stream as host
2. Tap "Share Screen" button
3. Grant screen sharing permissions
4. Verify screen share starts
5. Join as a viewer
6. Verify viewer can see screen share

**Expected Results:**
- ✅ Screen sharing starts successfully
- ✅ Viewers can see the shared screen
- ✅ Screen share quality is acceptable
- ✅ Screen share can be stopped

#### Test Case 6.2: Screen Share with Audio
**Objective:** Verify screen sharing includes audio

**Steps:**
1. Start a live stream as host
2. Start screen sharing
3. Play audio on the shared screen
4. Join as a viewer
5. Verify audio is transmitted

**Expected Results:**
- ✅ Audio is transmitted with screen share
- ✅ Audio quality is acceptable
- ✅ No audio delays or distortion

### 7. Performance Testing

#### Test Case 7.1: Multiple Concurrent Viewers
**Objective:** Verify system performance with multiple viewers

**Steps:**
1. Start a live stream as host
2. Join with 10+ devices as viewers
3. Send messages and reactions from all devices
4. Monitor system performance
5. Check for any crashes or delays

**Expected Results:**
- ✅ System handles 10+ concurrent viewers
- ✅ No significant performance degradation
- ✅ All features work correctly
- ✅ No crashes or freezes

#### Test Case 7.2: Long Duration Stream
**Objective:** Verify system stability during long streams

**Steps:**
1. Start a live stream as host
2. Keep stream running for 2+ hours
3. Monitor system resources
4. Check for memory leaks or performance issues

**Expected Results:**
- ✅ Stream remains stable for 2+ hours
- ✅ No memory leaks
- ✅ Performance remains consistent
- ✅ No crashes or freezes

### 8. Error Handling Testing

#### Test Case 8.1: Network Interruption
**Objective:** Verify system handles network interruptions gracefully

**Steps:**
1. Start a live stream as host
2. Join as a viewer
3. Disconnect network on viewer device
4. Reconnect network
5. Verify viewer can rejoin

**Expected Results:**
- ✅ System detects network interruption
- ✅ Viewer can rejoin after reconnection
- ✅ No data loss
- ✅ Stream continues for other viewers

#### Test Case 8.2: Permission Denied
**Objective:** Verify system handles permission denials gracefully

**Steps:**
1. Start a live stream as host
2. Deny camera permission
3. Verify error handling
4. Grant permission and retry

**Expected Results:**
- ✅ Clear error message displayed
- ✅ User can retry after granting permission
- ✅ No crashes or freezes

---

## 🤖 Automated Testing

### Unit Tests

#### Test File: `AdvancedLiveStreaming.test.tsx`
```typescript
import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import AdvancedLiveStreaming from '../AdvancedLiveStreaming';

describe('AdvancedLiveStreaming', () => {
  it('renders correctly when visible', () => {
    const { getByText } = render(
      <AdvancedLiveStreaming
        visible={true}
        onClose={jest.fn()}
        circleId="1"
        isHost={true}
        circleName="Test Circle"
      />
    );
    
    expect(getByText('Test Circle')).toBeTruthy();
  });

  it('calls onClose when close button is pressed', () => {
    const onClose = jest.fn();
    const { getByTestId } = render(
      <AdvancedLiveStreaming
        visible={true}
        onClose={onClose}
        circleId="1"
        isHost={true}
        circleName="Test Circle"
      />
    );
    
    fireEvent.press(getByTestId('close-button'));
    expect(onClose).toHaveBeenCalled();
  });

  it('displays host controls when isHost is true', () => {
    const { getByText } = render(
      <AdvancedLiveStreaming
        visible={true}
        onClose={jest.fn()}
        circleId="1"
        isHost={true}
        circleName="Test Circle"
      />
    );
    
    expect(getByText('Start Stream')).toBeTruthy();
  });

  it('displays viewer controls when isHost is false', () => {
    const { getByText } = render(
      <AdvancedLiveStreaming
        visible={true}
        onClose={jest.fn()}
        circleId="1"
        isHost={false}
        circleName="Test Circle"
      />
    );
    
    expect(getByText('Join Stream')).toBeTruthy();
  });
});
```

#### Test File: `LiveStreamingAPI.test.ts`
```typescript
import { createStream, joinStream, sendMessage, sendReaction } from '../api/liveStreaming';

describe('Live Streaming API', () => {
  beforeEach(() => {
    // Mock fetch
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('creates a stream successfully', async () => {
    const mockResponse = {
      success: true,
      data: {
        id: 'stream-123',
        title: 'Test Stream',
        status: 'scheduled'
      }
    };

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse)
    });

    const result = await createStream({
      title: 'Test Stream',
      circle_id: 1,
      category: 'general'
    });

    expect(result).toEqual(mockResponse.data);
    expect(global.fetch).toHaveBeenCalledWith(
      'http://192.168.1.236:8000/api/live-streams/',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json'
        })
      })
    );
  });

  it('handles API errors gracefully', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({
        success: false,
        error: 'Invalid request'
      })
    });

    await expect(createStream({
      title: '',
      circle_id: 1,
      category: 'general'
    })).rejects.toThrow('Invalid request');
  });
});
```

### Integration Tests

#### Test File: `LiveStreamingIntegration.test.ts`
```typescript
import { createStream, joinStream, sendMessage, sendReaction } from '../api/liveStreaming';

describe('Live Streaming Integration', () => {
  it('completes full streaming flow', async () => {
    // 1. Create stream
    const stream = await createStream({
      title: 'Integration Test Stream',
      circle_id: 1,
      category: 'general'
    });

    expect(stream.id).toBeDefined();
    expect(stream.status).toBe('scheduled');

    // 2. Start stream
    const startedStream = await startStream(stream.id);
    expect(startedStream.status).toBe('live');

    // 3. Join stream
    const viewer = await joinStream(stream.id);
    expect(viewer.viewer_id).toBeDefined();

    // 4. Send message
    const message = await sendMessage(stream.id, 'Hello from integration test!');
    expect(message.id).toBeDefined();

    // 5. Send reaction
    const reaction = await sendReaction(stream.id, 'fire');
    expect(reaction.id).toBeDefined();

    // 6. End stream
    const endedStream = await endStream(stream.id);
    expect(endedStream.status).toBe('ended');
  });
});
```

---

## 📊 Performance Testing

### Load Testing Script
```javascript
// load-test.js
const WebSocket = require('ws');
const fetch = require('node-fetch');

class LoadTester {
  constructor(baseUrl, numViewers = 50) {
    this.baseUrl = baseUrl;
    this.numViewers = numViewers;
    this.viewers = [];
  }

  async createStream() {
    const response = await fetch(`${this.baseUrl}/api/live-streams/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-token'
      },
      body: JSON.stringify({
        title: 'Load Test Stream',
        circle_id: 1,
        category: 'general'
      })
    });

    const data = await response.json();
    return data.data;
  }

  async startStream(streamId) {
    const response = await fetch(`${this.baseUrl}/api/live-streams/${streamId}/start/`, {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer test-token'
      }
    });

    const data = await response.json();
    return data.data;
  }

  async simulateViewers(streamId) {
    const promises = [];
    
    for (let i = 0; i < this.numViewers; i++) {
      promises.push(this.simulateViewer(streamId, i));
    }

    await Promise.all(promises);
  }

  async simulateViewer(streamId, viewerId) {
    // Join stream
    await fetch(`${this.baseUrl}/api/live-streams/${streamId}/join/`, {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer test-token'
      }
    });

    // Send messages
    setInterval(async () => {
      await fetch(`${this.baseUrl}/api/live-streams/${streamId}/messages/send/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token'
        },
        body: JSON.stringify({
          content: `Message from viewer ${viewerId}`
        })
      });
    }, 5000);

    // Send reactions
    setInterval(async () => {
      const reactions = ['heart', 'fire', 'money', 'thumbs'];
      const reaction = reactions[Math.floor(Math.random() * reactions.length)];
      
      await fetch(`${this.baseUrl}/api/live-streams/${streamId}/reactions/send/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token'
        },
        body: JSON.stringify({
          reaction_type: reaction
        })
      });
    }, 3000);
  }

  async runLoadTest() {
    console.log('Starting load test...');
    
    // Create and start stream
    const stream = await this.createStream();
    const startedStream = await this.startStream(stream.id);
    
    console.log(`Stream started: ${startedStream.id}`);
    
    // Simulate viewers
    await this.simulateViewers(stream.id);
    
    console.log(`Load test running with ${this.numViewers} viewers`);
    console.log('Press Ctrl+C to stop');
  }
}

// Run load test
const tester = new LoadTester('http://192.168.1.236:8000', 50);
tester.runLoadTest().catch(console.error);
```

---

## 🐛 Bug Reporting Template

### Bug Report Format
```
**Bug Title:** [Brief description of the bug]

**Severity:** [Critical/High/Medium/Low]

**Environment:**
- Device: [iPhone 12, Android Pixel 5, etc.]
- OS Version: [iOS 15.0, Android 11, etc.]
- App Version: [1.0.0]
- Network: [WiFi, 4G, 5G]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Result:**
[What should happen]

**Actual Result:**
[What actually happens]

**Screenshots/Videos:**
[Attach relevant media]

**Additional Notes:**
[Any other relevant information]
```

### Example Bug Report
```
**Bug Title:** Live stream crashes when viewer count exceeds 20

**Severity:** High

**Environment:**
- Device: iPhone 12
- OS Version: iOS 15.0
- App Version: 1.0.0
- Network: WiFi

**Steps to Reproduce:**
1. Start a live stream as host
2. Join with 20+ viewers
3. Send messages and reactions from multiple viewers
4. App crashes after 2-3 minutes

**Expected Result:**
App should handle 20+ viewers without crashing

**Actual Result:**
App crashes with "Out of memory" error

**Screenshots/Videos:**
[Attach crash logs and screenshots]

**Additional Notes:**
This only happens on iOS devices. Android devices work fine.
```

---

## ✅ Testing Checklist

### Pre-Release Testing
- [ ] All manual test cases pass
- [ ] Unit tests have 90%+ coverage
- [ ] Integration tests pass
- [ ] Load testing with 50+ concurrent users
- [ ] Performance testing for 2+ hour streams
- [ ] Error handling scenarios tested
- [ ] Network interruption scenarios tested
- [ ] Permission denial scenarios tested
- [ ] Cross-platform testing (iOS/Android)
- [ ] Different network conditions tested

### Post-Release Monitoring
- [ ] Monitor crash rates
- [ ] Monitor performance metrics
- [ ] Monitor user engagement
- [ ] Monitor error logs
- [ ] Monitor server resources
- [ ] Monitor network usage
- [ ] Monitor battery usage
- [ ] Monitor data usage

---

## 🚀 Deployment Testing

### Staging Environment
1. Deploy to staging environment
2. Run full test suite
3. Test with real devices
4. Test with different network conditions
5. Test with different user scenarios

### Production Deployment
1. Deploy to production
2. Monitor system metrics
3. Monitor user feedback
4. Monitor error rates
5. Monitor performance

---

## 📈 Success Metrics

### Performance Metrics
- Stream start time: < 5 seconds
- Message latency: < 1 second
- Reaction latency: < 500ms
- Poll response time: < 2 seconds
- Screen share latency: < 2 seconds

### Reliability Metrics
- Stream uptime: > 99%
- Message delivery rate: > 99%
- Reaction delivery rate: > 99%
- Poll accuracy: 100%
- Q&A response rate: > 95%

### User Experience Metrics
- User satisfaction: > 4.5/5
- Feature adoption rate: > 80%
- User retention: > 70%
- Support ticket volume: < 5% of users

---

## 🔧 Troubleshooting Guide

### Common Issues

#### Stream Won't Start
**Symptoms:** Stream fails to start, shows error message
**Solutions:**
1. Check camera/microphone permissions
2. Verify network connection
3. Restart the app
4. Check server status

#### Poor Video Quality
**Symptoms:** Video is pixelated or choppy
**Solutions:**
1. Check network speed
2. Reduce stream quality
3. Close other apps
4. Move closer to WiFi router

#### Chat Messages Not Sending
**Symptoms:** Messages don't appear for other users
**Solutions:**
1. Check network connection
2. Refresh the stream
3. Restart the app
4. Check server status

#### Reactions Not Working
**Symptoms:** Reactions don't appear on screen
**Solutions:**
1. Check network connection
2. Verify reaction permissions
3. Restart the app
4. Check server status

---

## 📞 Support and Escalation

### Level 1 Support
- Basic troubleshooting
- User guidance
- Common issue resolution

### Level 2 Support
- Technical issues
- Performance problems
- Integration issues

### Level 3 Support
- Critical bugs
- System failures
- Security issues

### Emergency Escalation
- System downtime
- Data loss
- Security breaches
- Critical performance issues

---

## 📚 Additional Resources

### Documentation
- [Live Streaming API Documentation](./LIVE_STREAMING_API_DOCUMENTATION.md)
- [Live Streaming Enhancements](./LIVE_STREAMING_ENHANCEMENTS.md)
- [Django Backend Setup](./backend/README.md)
- [React Native Setup](./mobile/README.md)

### Tools
- [Postman Collection](./postman/LiveStreamingAPI.postman_collection.json)
- [Load Testing Scripts](./scripts/load-test.js)
- [Monitoring Dashboard](./monitoring/dashboard.html)

### Contact
- Development Team: dev@richesreach.com
- QA Team: qa@richesreach.com
- Support Team: support@richesreach.com
