# RichesReach Testing Guide

Comprehensive testing guide for the self-hosted video chat and voice transcription features.

## 🧪 Test Overview

This guide covers testing for:
- **Video Chat**: WebRTC peer-to-peer video calls
- **Voice Transcription**: Whisper-based speech-to-text
- **WebRTC Signaling**: Socket.io call management
- **Mobile App Integration**: React Native components
- **Backend Services**: Node.js and Django APIs

## 🚀 Quick Start

### Run All Tests
```bash
# From the RichesReach root directory
./run_tests.sh
```

### Run Individual Test Suites
```bash
# Mobile app tests
cd mobile && npm test

# Whisper server tests
cd whisper-server && npm test

# Django backend tests
cd backend/backend && python manage.py test
```

## 📱 Mobile App Tests

### Test Files
- `mobile/src/features/community/screens/__tests__/CircleDetailScreenSelfHosted.test.tsx`
- `mobile/src/services/__tests__/WebRTCService.test.ts`
- `mobile/src/features/community/screens/__tests__/VoiceTranscription.test.ts`

### Test Coverage
- **Component Rendering**: Video call UI, microphone button, media pickers
- **Video Chat**: Call initiation, answering, ICE candidates, connection states
- **Voice Recording**: Audio permissions, recording lifecycle, transcription API
- **Error Handling**: Network errors, permission denials, API failures
- **State Management**: Call states, recording states, media selection

### Running Mobile Tests
```bash
cd mobile
npm install
npm test -- --coverage --watchAll=false
```

### Test Scenarios

#### Video Chat Tests
```typescript
// Test call initiation
it('should start video call successfully', async () => {
  const callButton = getByText('📹 Call');
  await act(async () => {
    fireEvent.press(callButton);
  });
  expect(queryByText('Video Call with partner-user-id')).toBeTruthy();
});

// Test incoming call handling
it('should handle incoming call offer', async () => {
  // Simulate incoming call
  const callOfferHandler = mockSocket.on.mock.calls.find(
    call => call[0] === 'call-offer'
  )?.[1];
  
  if (callOfferHandler) {
    callOfferHandler({
      offer: { type: 'offer', sdp: 'test-sdp' },
      from: 'test-user'
    });
  }
  
  expect(Alert.alert).toHaveBeenCalledWith(
    'Incoming Call',
    'test-user is calling. Answer?',
    expect.any(Array)
  );
});
```

#### Voice Transcription Tests
```typescript
// Test recording permissions
it('should request microphone permissions', async () => {
  const micButton = getByText('🎤');
  await act(async () => {
    fireEvent.press(micButton);
  });
  expect(Audio.requestPermissionsAsync).toHaveBeenCalled();
});

// Test transcription API
it('should send audio to transcription API', async () => {
  const mockResponse = {
    ok: true,
    json: async () => ({
      transcription: 'This is a test transcription',
      audioUrl: '/uploads/test-audio.m4a',
      processingTime: 1500,
    }),
  };
  
  (global.fetch as jest.Mock).mockResolvedValue(mockResponse);
  
  // Test transcription flow
  const result = await response.json();
  expect(result.transcription).toBe('This is a test transcription');
});
```

## 🎤 Whisper Server Tests

### Test Files
- `whisper-server/__tests__/server.test.js`

### Test Coverage
- **API Endpoints**: Transcription, posts, comments, media upload
- **Socket.io Events**: Video call signaling, live streaming, chat
- **Authentication**: JWT token validation, rate limiting
- **File Handling**: Audio upload, format validation, size limits
- **Error Handling**: Network errors, missing models, invalid requests

### Running Server Tests
```bash
cd whisper-server
npm install
npm test
```

### Test Scenarios

#### Transcription API Tests
```javascript
// Test successful transcription
it('should transcribe audio successfully', async () => {
  const validToken = jwt.sign(
    { id: 'test-user', email: 'test@example.com' },
    process.env.JWT_SECRET || 'test-secret'
  );

  const response = await request(app)
    .post('/api/transcribe-audio/')
    .set('Authorization', `Bearer ${validToken}`)
    .attach('audio', Buffer.from('fake audio data'), 'test.m4a')
    .expect(200);

  expect(response.body).toHaveProperty('transcription');
  expect(response.body).toHaveProperty('audioUrl');
  expect(response.body).toHaveProperty('processingTime');
});

// Test authentication
it('should reject requests without authentication', async () => {
  await request(app)
    .post('/api/transcribe-audio/')
    .attach('audio', Buffer.from('fake audio data'), 'test.m4a')
    .expect(401);
});
```

#### Socket.io Signaling Tests
```javascript
// Test call offer handling
it('should handle call offer', (done) => {
  const callOffer = {
    offer: { type: 'offer', sdp: 'test-sdp' },
    to: 'target-user',
    from: 'caller-user'
  };

  serverSocket.on('call-offer', (data) => {
    expect(data).toEqual(callOffer);
    done();
  });

  clientSocket.emit('call-offer', callOffer);
});
```

## 🔗 Integration Tests

### Server Connectivity
```bash
# Test Whisper server health
curl http://localhost:3001/health

# Test Django backend health
curl http://localhost:8000/health

# Test transcription endpoint
curl -X POST http://localhost:3001/api/transcribe-audio/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "audio=@test-audio.m4a"
```

### Video Chat Flow
1. **Start both servers**:
   ```bash
   # Terminal 1: Whisper server
   cd whisper-server && npm start
   
   # Terminal 2: Django backend
   cd backend/backend && python manage.py runserver
   ```

2. **Test call signaling**:
   ```bash
   # Use WebSocket client to test signaling
   wscat -c ws://localhost:3001
   ```

3. **Test mobile app**:
   ```bash
   # Build and run mobile app
   cd mobile && eas build --platform android --profile development
   ```

## 🎯 Manual Testing Scenarios

### Video Chat Testing

#### 1. Call Initiation
- [ ] Tap "📹 Call" button in wealth circle
- [ ] Verify call modal opens
- [ ] Check camera/microphone permissions
- [ ] Verify local video stream appears

#### 2. Call Answering
- [ ] Receive incoming call notification
- [ ] Accept call from alert dialog
- [ ] Verify remote video stream appears
- [ ] Test call controls (mute, video toggle, end)

#### 3. Call Quality
- [ ] Test with different network conditions
- [ ] Verify audio/video synchronization
- [ ] Test call duration (5+ minutes)
- [ ] Check connection stability

### Voice Transcription Testing

#### 1. Recording
- [ ] Tap microphone button
- [ ] Verify recording starts (visual feedback)
- [ ] Record 10-30 second audio
- [ ] Stop recording and verify transcription

#### 2. Transcription Accuracy
- [ ] Test with clear speech
- [ ] Test with background noise
- [ ] Test with financial terminology
- [ ] Verify processing time (<5 seconds)

#### 3. Error Handling
- [ ] Test without microphone permission
- [ ] Test with network disconnected
- [ ] Test with invalid audio format
- [ ] Test with large audio files

## 🔒 Security Testing

### Authentication
```bash
# Test invalid JWT
curl -X POST http://localhost:3001/api/transcribe-audio/ \
  -H "Authorization: Bearer invalid-token" \
  -F "audio=@test.m4a"
# Expected: 401 Unauthorized

# Test missing JWT
curl -X POST http://localhost:3001/api/transcribe-audio/ \
  -F "audio=@test.m4a"
# Expected: 401 Unauthorized
```

### Rate Limiting
```bash
# Test rate limiting (make 60+ requests quickly)
for i in {1..65}; do
  curl -X POST http://localhost:3001/api/transcribe-audio/ \
    -H "Authorization: Bearer $VALID_TOKEN" \
    -F "audio=@test.m4a"
done
# Expected: Some requests should return 429 Too Many Requests
```

### File Upload Security
```bash
# Test file size limits
dd if=/dev/zero of=large-file.m4a bs=1M count=30
curl -X POST http://localhost:3001/api/transcribe-audio/ \
  -H "Authorization: Bearer $VALID_TOKEN" \
  -F "audio=@large-file.m4a"
# Expected: 400 Bad Request (file too large)

# Test invalid file types
echo "not audio" > test.txt
curl -X POST http://localhost:3001/api/transcribe-audio/ \
  -H "Authorization: Bearer $VALID_TOKEN" \
  -F "audio=@test.txt"
# Expected: 400 Bad Request (invalid file type)
```

## ⚡ Performance Testing

### Load Testing
```bash
# Install artillery for load testing
npm install -g artillery

# Create load test config
cat > load-test.yml << EOF
config:
  target: 'http://localhost:3001'
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - name: "Transcription Load Test"
    requests:
      - post:
          url: "/api/transcribe-audio/"
          headers:
            Authorization: "Bearer $VALID_TOKEN"
          formData:
            audio: "@test-audio.m4a"
EOF

# Run load test
artillery run load-test.yml
```

### Memory Testing
```bash
# Monitor memory usage during tests
# Use htop or Activity Monitor to watch:
# - Node.js process memory
# - Whisper model memory usage
# - Audio processing memory
```

## 🐛 Debugging Tests

### Common Issues

#### 1. Test Timeouts
```javascript
// Increase timeout for slow tests
jest.setTimeout(30000);

// Or for specific tests
it('should handle slow operation', async () => {
  // Test code
}, 30000);
```

#### 2. Mock Issues
```javascript
// Clear mocks between tests
beforeEach(() => {
  jest.clearAllMocks();
});

// Reset modules if needed
beforeEach(() => {
  jest.resetModules();
});
```

#### 3. Async Issues
```javascript
// Use waitFor for async operations
await waitFor(() => {
  expect(getByText('Expected Text')).toBeTruthy();
});

// Use act for state updates
await act(async () => {
  fireEvent.press(button);
});
```

### Debug Commands
```bash
# Run tests with verbose output
npm test -- --verbose

# Run specific test file
npm test -- CircleDetailScreenSelfHosted.test.tsx

# Run tests in watch mode
npm test -- --watch

# Generate coverage report
npm test -- --coverage
```

## 📊 Test Metrics

### Coverage Targets
- **Unit Tests**: >80% code coverage
- **Integration Tests**: >70% API endpoint coverage
- **E2E Tests**: Critical user flows covered

### Performance Targets
- **Video Call Connection**: <2 seconds
- **Voice Transcription**: <5 seconds
- **API Response Time**: <1 second
- **Memory Usage**: <100MB per service

## 🎉 Test Success Criteria

### All Tests Pass When:
- [ ] Mobile app unit tests pass
- [ ] Whisper server tests pass
- [ ] Django backend tests pass
- [ ] Integration tests pass
- [ ] Security tests pass
- [ ] Performance tests meet targets

### Ready for Production When:
- [ ] All automated tests pass
- [ ] Manual testing scenarios completed
- [ ] Security vulnerabilities addressed
- [ ] Performance benchmarks met
- [ ] Error handling verified
- [ ] Documentation updated

## 🔧 Troubleshooting

### Test Environment Issues
```bash
# Clear Jest cache
npm test -- --clearCache

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+
```

### Server Issues
```bash
# Check if ports are available
lsof -i :3001  # Whisper server
lsof -i :8000  # Django backend

# Check server logs
tail -f whisper-server/logs/server.log
tail -f backend/logs/django.log
```

### Mobile App Issues
```bash
# Clear Expo cache
expo r -c

# Reset Metro bundler
npx react-native start --reset-cache

# Check EAS build status
eas build:list
```

This comprehensive testing guide ensures your RichesReach implementation is robust, secure, and ready for production use!