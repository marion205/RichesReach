// Self-hosted Whisper transcription server for RichesReach
require('dotenv').config();
const express = require('express');
const multer = require('multer');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');
const jwt = require('jsonwebtoken');
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const ffmpeg = require('fluent-ffmpeg');
const mongoose = require('mongoose');
const { Expo } = require('expo-server-sdk');

const app = express();
const server = http.createServer(app);
const io = new Server(server, { 
  cors: { 
    origin: process.env.ALLOWED_ORIGINS?.split(',') || '*',
    methods: ['GET', 'POST']
  } 
});

const execAsync = promisify(exec);
const expo = new Expo();

// Security middleware
app.use(helmet());
app.use(compression());
app.use(morgan('combined'));

// Rate limiting
const transcriptionLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 50, // limit each IP to 50 requests per windowMs
  message: 'Too many transcription requests, please try again later.'
});

// CORS and body parsing
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use('/uploads', express.static('uploads'));

// Ensure uploads directory exists
if (!fs.existsSync('uploads')) {
  fs.mkdirSync('uploads', { recursive: true });
}

// Ensure models directory exists
if (!fs.existsSync('models')) {
  fs.mkdirSync('models', { recursive: true });
}

// Multer configuration for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({ 
  storage,
  limits: {
    fileSize: 25 * 1024 * 1024, // 25MB limit
  },
  fileFilter: (req, file, cb) => {
    const allowedMimes = [
      'audio/mpeg', 'audio/mp3', 'audio/mp4', 'audio/m4a', 
      'audio/wav', 'audio/webm', 'audio/ogg', 'audio/aac'
    ];
    if (allowedMimes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Invalid file type. Only audio files are allowed.'), false);
    }
  }
});

// Database connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/richesreach_whisper', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

// Models
const Message = mongoose.model('Message', {
  content: String,
  user: String,
  room: String,
  timestamp: Date,
  type: { type: String, default: 'text' },
  mediaUrl: String
});

const Transcription = mongoose.model('Transcription', {
  userId: String,
  originalFilename: String,
  transcription: String,
  audioUrl: String,
  processingTime: Number,
  model: String,
  timestamp: Date
});

// JWT Authentication middleware
const authenticate = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) {
    return res.status(401).json({ error: 'No token provided' });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Invalid token' });
  }
};

// Whisper model configuration
const WHISPER_MODEL = process.env.WHISPER_MODEL || 'ggml-tiny.en-q5_0.bin';
const WHISPER_PATH = process.env.WHISPER_PATH || './whisper.cpp';
const MODEL_PATH = path.join(__dirname, 'models', WHISPER_MODEL);

// Check if Whisper model exists
const checkWhisperModel = async () => {
  if (!fs.existsSync(MODEL_PATH)) {
    console.warn(`⚠️  Whisper model not found at ${MODEL_PATH}`);
    console.log('📥 Run "npm run setup-whisper" to download and quantize the model');
    return false;
  }
  return true;
};

// Convert audio to WAV format for Whisper
const convertToWav = async (inputPath, outputPath) => {
  return new Promise((resolve, reject) => {
    ffmpeg(inputPath)
      .audioChannels(1)
      .audioFrequency(16000)
      .audioCodec('pcm_s16le')
      .format('wav')
      .on('end', () => resolve(outputPath))
      .on('error', (err) => reject(err))
      .save(outputPath);
  });
};

// Transcribe audio using Whisper.cpp
const transcribeAudio = async (audioPath) => {
  const startTime = Date.now();
  
  try {
    // Convert to WAV if needed
    const wavPath = audioPath.replace(/\.[^/.]+$/, '.wav');
    await convertToWav(audioPath, wavPath);
    
    // Run Whisper.cpp
    const whisperCmd = `${WHISPER_PATH}/main -m ${MODEL_PATH} -f ${wavPath} --language en --no-timestamps --print-colors false`;
    const { stdout } = await execAsync(whisperCmd);
    
    // Clean up WAV file
    if (fs.existsSync(wavPath)) {
      fs.unlinkSync(wavPath);
    }
    
    const transcription = stdout.trim();
    const processingTime = Date.now() - startTime;
    
    return { transcription, processingTime };
  } catch (error) {
    console.error('Whisper transcription error:', error);
    throw new Error(`Transcription failed: ${error.message}`);
  }
};

// Socket.io for real-time features
io.on('connection', (socket) => {
  console.log('🔌 Client connected:', socket.id);
  
  socket.on('join_circle', ({ circleId }) => {
    socket.join(circleId);
    console.log(`👥 User ${socket.id} joined circle ${circleId}`);
  });
  
  // Fireside Room handlers (WebRTC signaling)
  socket.on('join-room', ({ room }) => {
    socket.join(room);
    console.log(`🔥 [Fireside] User ${socket.id} joined room ${room}`);
    // Notify others in the room
    socket.to(room).emit('user-joined', { userId: socket.id, room });
  });
  
  socket.on('leave-room', ({ room }) => {
    socket.leave(room);
    console.log(`🔥 [Fireside] User ${socket.id} left room ${room}`);
    socket.to(room).emit('user-left', { userId: socket.id, room });
  });
  
  // WebRTC signaling for Fireside Room
  socket.on('offer', ({ from, offer, to }) => {
    console.log(`📞 [Fireside] Offer from ${from} to ${to || 'all'}`);
    if (to) {
      socket.to(to).emit('offer', { from, offer });
    } else {
      // Broadcast to room if no specific target
      socket.broadcast.emit('offer', { from, offer });
    }
  });
  
  socket.on('answer', ({ from, answer, to }) => {
    console.log(`📞 [Fireside] Answer from ${from} to ${to || 'all'}`);
    if (to) {
      socket.to(to).emit('answer', { from, answer });
    } else {
      socket.broadcast.emit('answer', { from, answer });
    }
  });
  
  socket.on('ice-candidate', ({ candidate, to }) => {
    if (to) {
      socket.to(to).emit('ice-candidate', { candidate, from: socket.id });
    } else {
      socket.broadcast.emit('ice-candidate', { candidate, from: socket.id });
    }
  });
  
  socket.on('start_live_stream', ({ circleId, host }) => {
    socket.to(circleId).emit('live_stream_started', { host, channelId: circleId });
    console.log(`📺 Live stream started in circle ${circleId} by ${host}`);
  });
  
  socket.on('join_live_stream', ({ circleId, viewer }) => {
    socket.to(circleId).emit('viewer-joined', { viewer });
    const count = io.sockets.adapter.rooms.get(circleId)?.size || 0;
    socket.to(circleId).emit('viewer_count_update', { count });
    console.log(`👀 Viewer ${viewer} joined live stream in circle ${circleId}`);
  });
  
  socket.on('end_live_stream', ({ circleId }) => {
    socket.to(circleId).emit('end_live_stream', {});
    console.log(`📺 Live stream ended in circle ${circleId}`);
  });
  
  socket.on('new_post', (newPost) => {
    socket.to(newPost.circleId).emit('new_post', newPost);
    console.log(`📝 New post in circle ${newPost.circleId}`);
  });
  
  socket.on('new_comment', ({ postId, comment, circleId }) => {
    socket.to(circleId).emit('new_comment', { postId, comment });
    console.log(`💬 New comment on post ${postId} in circle ${circleId}`);
  });
  
  socket.on('disconnect', () => {
    console.log('🔌 Client disconnected:', socket.id);
  });

  // Video call signaling handlers
  socket.on('call-offer', ({ offer, to, from }) => {
    console.log(`📞 Call offer from ${from} to ${to}`);
    socket.to(to).emit('call-offer', { offer, from });
  });

  socket.on('call-answer', ({ answer, to }) => {
    console.log(`📞 Call answer to ${to}`);
    socket.to(to).emit('call-answer', { answer });
  });

  socket.on('ice-candidate', ({ candidate, to }) => {
    socket.to(to).emit('ice-candidate', { candidate });
  });

  socket.on('call-decline', ({ to }) => {
    console.log(`📞 Call declined to ${to}`);
    socket.to(to).emit('call-decline', {});
  });

  socket.on('end-call', ({ to }) => {
    console.log(`📞 Call ended to ${to}`);
    socket.to(to).emit('end-call', {});
  });
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    whisperModel: WHISPER_MODEL,
    modelExists: fs.existsSync(MODEL_PATH)
  });
});

// POST /api/transcribe-audio/ - Main transcription endpoint
app.post('/api/transcribe-audio/', transcriptionLimiter, authenticate, upload.single('audio'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No audio file uploaded' });
  }

  const audioPath = req.file.path;
  const audioUrl = `/uploads/${req.file.filename}`;

  try {
    // Check if Whisper model exists
    if (!await checkWhisperModel()) {
      return res.status(503).json({ 
        error: 'Whisper model not available. Please run setup.',
        setupCommand: 'npm run setup-whisper'
      });
    }

    console.log(`🎤 Transcribing audio: ${req.file.originalname}`);
    
    // Transcribe audio
    const { transcription, processingTime } = await transcribeAudio(audioPath);
    
    // Save transcription record
    const transcriptionRecord = new Transcription({
      userId: req.user.id,
      originalFilename: req.file.originalname,
      transcription,
      audioUrl,
      processingTime,
      model: WHISPER_MODEL,
      timestamp: new Date()
    });
    await transcriptionRecord.save();
    
    console.log(`✅ Transcription completed in ${processingTime}ms: "${transcription}"`);
    
    res.json({ 
      transcription, 
      audioUrl,
      processingTime,
      model: WHISPER_MODEL
    });
    
  } catch (error) {
    console.error('Transcription error:', error);
    
    // Clean up uploaded file on error
    if (fs.existsSync(audioPath)) {
      fs.unlinkSync(audioPath);
    }
    
    res.status(500).json({ 
      error: 'Transcription failed', 
      details: error.message 
    });
  }
});

// POST /api/wealth-circles/:id/posts/ - Create post with optional transcription
app.post('/api/wealth-circles/:id/posts/', authenticate, async (req, res) => {
  const { id } = req.params;
  const { content, media, transcription } = req.body;
  
  const newPost = {
    id: Date.now().toString(),
    content: content || transcription,
    media,
    user: req.user,
    timestamp: new Date().toISOString(),
    likes: 0,
    comments: 0,
    circleId: id,
  };
  
  // Emit real-time update
  io.to(id).emit('new_post', newPost);
  
  console.log(`📝 New post created in circle ${id}`);
  res.json(newPost);
});

// POST /api/posts/:id/comments/ - Add comment to post
app.post('/api/posts/:id/comments/', authenticate, async (req, res) => {
  const { id } = req.params;
  const { content } = req.body;
  
  const comment = {
    id: Date.now().toString(),
    content,
    user: req.user,
    timestamp: new Date().toISOString(),
    likes: 0,
  };
  
  // Emit real-time update
  io.to(req.body.circleId).emit('new_comment', { postId: id, comment });
  
  console.log(`💬 New comment added to post ${id}`);
  res.json(comment);
});

// POST /api/upload-media/ - Upload media files
app.post('/api/upload-media/', authenticate, upload.single('media'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No media file uploaded' });
  }
  
  const mediaUrl = `/uploads/${req.file.filename}`;
  const type = req.file.mimetype.startsWith('video') ? 'video' : 
               req.file.mimetype.startsWith('audio') ? 'audio' : 'image';
  
  res.json({ mediaUrl, type });
});

// GET /api/wealth-circles/:id/posts/ - Get posts for circle
app.get('/api/wealth-circles/:id/posts/', authenticate, async (req, res) => {
  const { id } = req.params;
  // In a real app, you'd fetch from database
  const mockPosts = [
    {
      id: '1',
      content: 'Welcome to our wealth circle! Share your insights and strategies.',
      user: { id: 'admin', name: 'Circle Admin', avatar: 'https://via.placeholder.com/40' },
      timestamp: new Date().toISOString(),
      likes: 5,
      comments: 2,
      circleId: id,
    }
  ];
  
  res.json(mockPosts);
});

// POST /api/register-push-token/ - Register for push notifications
app.post('/api/register-push-token/', authenticate, async (req, res) => {
  const { expoPushToken, circleId } = req.body;
  
  if (!Expo.isExpoPushToken(expoPushToken)) {
    return res.status(400).json({ error: 'Invalid Expo push token' });
  }
  
  // In a real app, save to database
  console.log(`📱 Push token registered for user ${req.user.id} in circle ${circleId}`);
  
  res.json({ success: true });
});

// Error handling middleware
app.use((error, req, res, next) => {
  if (error instanceof multer.MulterError) {
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({ error: 'File too large. Maximum size is 25MB.' });
    }
  }
  
  console.error('Server error:', error);
  res.status(500).json({ error: 'Internal server error' });
});

// Start server (skip when running under Jest)
const PORT = process.env.PORT || 3001;
if (process.env.NODE_ENV !== 'test') {
  server.listen(PORT, () => {
    console.log(`🚀 Whisper server running on port ${PORT}`);
    console.log(`🎤 Whisper model: ${WHISPER_MODEL}`);
    console.log(`📁 Model path: ${MODEL_PATH}`);
    console.log(`🔧 Whisper path: ${WHISPER_PATH}`);

    // Check model availability
    checkWhisperModel().then(exists => {
      if (exists) {
        console.log('✅ Whisper model ready');
      } else {
        console.log('⚠️  Whisper model not found - run setup');
      }
    });
  });
}

module.exports = { app, server, io };
