const request = require('supertest');
const express = require('express');
const { Server } = require('socket.io');
const http = require('http');
const fs = require('fs');
const path = require('path');
const jwt = require('jsonwebtoken');

// Mock dependencies
jest.mock('fs');
jest.mock('child_process');
jest.mock('fluent-ffmpeg');
jest.mock('mongoose');

// Import the server
const { app, server, io } = require('../server');

describe('Whisper Server', () => {
  let testServer;
  let testIO;
  let clientSocket;
  let serverSocket;

  beforeAll((done) => {
    testServer = http.createServer(app);
    testIO = new Server(testServer);
    
    testServer.listen(() => {
      const port = testServer.address().port;
      
      // Connect client socket
      clientSocket = require('socket.io-client')(`http://localhost:${port}`);
      
      testIO.on('connection', (socket) => {
        serverSocket = socket;
      });
      
      clientSocket.on('connect', done);
    });
  });

  afterAll((done) => {
    testIO.close();
    testServer.close(done);
  });

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock file system
    fs.existsSync.mockReturnValue(true);
    fs.mkdirSync.mockImplementation(() => {});
    fs.unlinkSync.mockImplementation(() => {});
    
    // Mock child_process
    const { exec } = require('child_process');
    exec.mockImplementation((command, callback) => {
      callback(null, { stdout: 'Test transcription result' });
    });
  });

  describe('Health Check Endpoint', () => {
    it('should return health status', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toHaveProperty('status', 'healthy');
      expect(response.body).toHaveProperty('timestamp');
      expect(response.body).toHaveProperty('whisperModel');
      expect(response.body).toHaveProperty('modelExists');
    });
  });

  describe('Transcription Endpoint', () => {
    const validToken = jwt.sign(
      { id: 'test-user', email: 'test@example.com' },
      process.env.JWT_SECRET || 'test-secret'
    );

    it('should transcribe audio successfully', async () => {
      // Mock successful transcription
      const { exec } = require('child_process');
      exec.mockImplementation((command, callback) => {
        callback(null, { stdout: 'This is a test transcription' });
      });

      const response = await request(app)
        .post('/api/transcribe-audio/')
        .set('Authorization', `Bearer ${validToken}`)
        .attach('audio', Buffer.from('fake audio data'), 'test.m4a')
        .expect(200);

      expect(response.body).toHaveProperty('transcription', 'This is a test transcription');
      expect(response.body).toHaveProperty('audioUrl');
      expect(response.body).toHaveProperty('processingTime');
      expect(response.body).toHaveProperty('model');
    });

    it('should reject requests without authentication', async () => {
      await request(app)
        .post('/api/transcribe-audio/')
        .attach('audio', Buffer.from('fake audio data'), 'test.m4a')
        .expect(401);
    });

    it('should reject requests without audio file', async () => {
      await request(app)
        .post('/api/transcribe-audio/')
        .set('Authorization', `Bearer ${validToken}`)
        .expect(400);
    });

    it('should handle transcription errors', async () => {
      // Mock transcription failure
      const { exec } = require('child_process');
      exec.mockImplementation((command, callback) => {
        callback(new Error('Whisper failed'), null);
      });

      await request(app)
        .post('/api/transcribe-audio/')
        .set('Authorization', `Bearer ${validToken}`)
        .attach('audio', Buffer.from('fake audio data'), 'test.m4a')
        .expect(500);
    });

    it('should handle missing Whisper model', async () => {
      // Mock missing model
      fs.existsSync.mockReturnValue(false);

      await request(app)
        .post('/api/transcribe-audio/')
        .set('Authorization', `Bearer ${validToken}`)
        .attach('audio', Buffer.from('fake audio data'), 'test.m4a')
        .expect(503);
    });

    it('should reject files that are too large', async () => {
      // Create a large buffer (26MB)
      const largeBuffer = Buffer.alloc(26 * 1024 * 1024);

      await request(app)
        .post('/api/transcribe-audio/')
        .set('Authorization', `Bearer ${validToken}`)
        .attach('audio', largeBuffer, 'large.m4a')
        .expect(400);
    });

    it('should reject invalid file types', async () => {
      await request(app)
        .post('/api/transcribe-audio/')
        .set('Authorization', `Bearer ${validToken}`)
        .attach('audio', Buffer.from('fake data'), 'test.txt')
        .expect(400);
    });
  });

  describe('Posts Endpoint', () => {
    const validToken = jwt.sign(
      { id: 'test-user', email: 'test@example.com' },
      process.env.JWT_SECRET || 'test-secret'
    );

    it('should create a new post', async () => {
      const postData = {
        content: 'Test post content',
        media: { url: '/uploads/test.jpg', type: 'image' }
      };

      const response = await request(app)
        .post('/api/wealth-circles/test-circle/posts/')
        .set('Authorization', `Bearer ${validToken}`)
        .send(postData)
        .expect(200);

      expect(response.body).toHaveProperty('id');
      expect(response.body).toHaveProperty('content', 'Test post content');
      expect(response.body).toHaveProperty('media');
      expect(response.body).toHaveProperty('user');
      expect(response.body).toHaveProperty('timestamp');
    });

    it('should get posts for a circle', async () => {
      const response = await request(app)
        .get('/api/wealth-circles/test-circle/posts/')
        .set('Authorization', `Bearer ${validToken}`)
        .expect(200);

      expect(Array.isArray(response.body)).toBe(true);
    });
  });

  describe('Comments Endpoint', () => {
    const validToken = jwt.sign(
      { id: 'test-user', email: 'test@example.com' },
      process.env.JWT_SECRET || 'test-secret'
    );

    it('should add a comment to a post', async () => {
      const commentData = {
        content: 'Test comment',
        circleId: 'test-circle'
      };

      const response = await request(app)
        .post('/api/posts/test-post/comments/')
        .set('Authorization', `Bearer ${validToken}`)
        .send(commentData)
        .expect(200);

      expect(response.body).toHaveProperty('id');
      expect(response.body).toHaveProperty('content', 'Test comment');
      expect(response.body).toHaveProperty('user');
      expect(response.body).toHaveProperty('timestamp');
    });
  });

  describe('Media Upload Endpoint', () => {
    const validToken = jwt.sign(
      { id: 'test-user', email: 'test@example.com' },
      process.env.JWT_SECRET || 'test-secret'
    );

    it('should upload media successfully', async () => {
      const response = await request(app)
        .post('/api/upload-media/')
        .set('Authorization', `Bearer ${validToken}`)
        .attach('media', Buffer.from('fake media data'), 'test.jpg')
        .expect(200);

      expect(response.body).toHaveProperty('mediaUrl');
      expect(response.body).toHaveProperty('type');
    });

    it('should reject uploads without authentication', async () => {
      await request(app)
        .post('/api/upload-media/')
        .attach('media', Buffer.from('fake media data'), 'test.jpg')
        .expect(401);
    });
  });

  describe('Push Token Registration', () => {
    const validToken = jwt.sign(
      { id: 'test-user', email: 'test@example.com' },
      process.env.JWT_SECRET || 'test-secret'
    );

    it('should register push token successfully', async () => {
      const tokenData = {
        expoPushToken: 'ExponentPushToken[test-token]',
        circleId: 'test-circle'
      };

      const response = await request(app)
        .post('/api/register-push-token/')
        .set('Authorization', `Bearer ${validToken}`)
        .send(tokenData)
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
    });

    it('should reject invalid push tokens', async () => {
      const tokenData = {
        expoPushToken: 'invalid-token',
        circleId: 'test-circle'
      };

      await request(app)
        .post('/api/register-push-token/')
        .set('Authorization', `Bearer ${validToken}`)
        .send(tokenData)
        .expect(400);
    });
  });

  describe('Socket.io Video Call Signaling', () => {
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

    it('should handle call answer', (done) => {
      const callAnswer = {
        answer: { type: 'answer', sdp: 'test-sdp' },
        to: 'caller-user'
      };

      serverSocket.on('call-answer', (data) => {
        expect(data).toEqual(callAnswer);
        done();
      });

      clientSocket.emit('call-answer', callAnswer);
    });

    it('should handle ICE candidate', (done) => {
      const iceCandidate = {
        candidate: { candidate: 'test-candidate', sdpMLineIndex: 0 },
        to: 'target-user'
      };

      serverSocket.on('ice-candidate', (data) => {
        expect(data).toEqual(iceCandidate);
        done();
      });

      clientSocket.emit('ice-candidate', iceCandidate);
    });

    it('should handle call decline', (done) => {
      const callDecline = {
        to: 'caller-user'
      };

      serverSocket.on('call-decline', (data) => {
        expect(data).toEqual(callDecline);
        done();
      });

      clientSocket.emit('call-decline', callDecline);
    });

    it('should handle end call', (done) => {
      const endCall = {
        to: 'target-user'
      };

      serverSocket.on('end-call', (data) => {
        expect(data).toEqual(endCall);
        done();
      });

      clientSocket.emit('end-call', endCall);
    });
  });

  describe('Socket.io Live Streaming', () => {
    it('should handle live stream start', (done) => {
      const streamData = {
        circleId: 'test-circle',
        host: 'test-host'
      };

      serverSocket.on('start_live_stream', (data) => {
        expect(data).toEqual(streamData);
        done();
      });

      clientSocket.emit('start_live_stream', streamData);
    });

    it('should handle live stream join', (done) => {
      const joinData = {
        circleId: 'test-circle',
        viewer: 'test-viewer'
      };

      serverSocket.on('join_live_stream', (data) => {
        expect(data).toEqual(joinData);
        done();
      });

      clientSocket.emit('join_live_stream', joinData);
    });

    it('should handle live stream end', (done) => {
      const endData = {
        circleId: 'test-circle'
      };

      serverSocket.on('end_live_stream', (data) => {
        expect(data).toEqual(endData);
        done();
      });

      clientSocket.emit('end_live_stream', endData);
    });
  });

  describe('Socket.io Chat', () => {
    it('should handle new post', (done) => {
      const postData = {
        id: 'test-post',
        content: 'Test post',
        circleId: 'test-circle'
      };

      serverSocket.on('new_post', (data) => {
        expect(data).toEqual(postData);
        done();
      });

      clientSocket.emit('new_post', postData);
    });

    it('should handle new comment', (done) => {
      const commentData = {
        postId: 'test-post',
        comment: { id: 'test-comment', content: 'Test comment' },
        circleId: 'test-circle'
      };

      serverSocket.on('new_comment', (data) => {
        expect(data).toEqual(commentData);
        done();
      });

      clientSocket.emit('new_comment', commentData);
    });
  });

  describe('Error Handling', () => {
    it('should handle invalid JWT tokens', async () => {
      await request(app)
        .post('/api/transcribe-audio/')
        .set('Authorization', 'Bearer invalid-token')
        .attach('audio', Buffer.from('fake audio data'), 'test.m4a')
        .expect(401);
    });

    it('should handle missing JWT tokens', async () => {
      await request(app)
        .post('/api/transcribe-audio/')
        .attach('audio', Buffer.from('fake audio data'), 'test.m4a')
        .expect(401);
    });

    it('should handle rate limiting', async () => {
      const validToken = jwt.sign(
        { id: 'test-user', email: 'test@example.com' },
        process.env.JWT_SECRET || 'test-secret'
      );

      // Make multiple requests to trigger rate limiting
      const promises = Array(60).fill().map(() =>
        request(app)
          .post('/api/transcribe-audio/')
          .set('Authorization', `Bearer ${validToken}`)
          .attach('audio', Buffer.from('fake audio data'), 'test.m4a')
      );

      const responses = await Promise.all(promises);
      const rateLimitedResponses = responses.filter(r => r.status === 429);
      
      expect(rateLimitedResponses.length).toBeGreaterThan(0);
    });
  });

  describe('File System Operations', () => {
    it('should create uploads directory if it does not exist', () => {
      fs.existsSync.mockReturnValue(false);
      
      // Re-import server to trigger directory creation
      jest.resetModules();
      require('../server');
      
      expect(fs.mkdirSync).toHaveBeenCalledWith('uploads', { recursive: true });
    });

    it('should create models directory if it does not exist', () => {
      fs.existsSync.mockReturnValue(false);
      
      // Re-import server to trigger directory creation
      jest.resetModules();
      require('../server');
      
      expect(fs.mkdirSync).toHaveBeenCalledWith('models', { recursive: true });
    });
  });

  describe('CORS Configuration', () => {
    it('should allow requests from allowed origins', async () => {
      const response = await request(app)
        .get('/health')
        .set('Origin', 'http://localhost:3000')
        .expect(200);

      expect(response.headers['access-control-allow-origin']).toBeDefined();
    });
  });

  describe('Security Headers', () => {
    it('should include security headers', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.headers['x-frame-options']).toBeDefined();
      expect(response.headers['x-content-type-options']).toBeDefined();
      expect(response.headers['x-xss-protection']).toBeDefined();
    });
  });
});
