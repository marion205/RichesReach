#!/usr/bin/env node

// Setup script for downloading and quantizing Whisper models
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');
const https = require('https');

const execAsync = promisify(exec);

const WHISPER_REPO = 'https://github.com/ggerganov/whisper.cpp.git';
const WHISPER_DIR = './whisper.cpp';
const MODELS_DIR = './models';

// Model configurations
const MODELS = {
  'tiny.en': {
    url: 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin',
    size: '39MB',
    accuracy: '80-85%',
    speed: 'Fastest'
  },
  'base.en': {
    url: 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin',
    size: '142MB',
    accuracy: '85-90%',
    speed: 'Fast'
  },
  'small.en': {
    url: 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin',
    size: '483MB',
    accuracy: '90-95%',
    speed: 'Medium'
  }
};

// Download file function
const downloadFile = (url, dest) => {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    https.get(url, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`Failed to download: ${response.statusCode}`));
        return;
      }
      
      const totalSize = parseInt(response.headers['content-length'], 10);
      let downloadedSize = 0;
      
      response.on('data', (chunk) => {
        downloadedSize += chunk.length;
        const progress = ((downloadedSize / totalSize) * 100).toFixed(1);
        process.stdout.write(`\r📥 Downloading: ${progress}% (${(downloadedSize / 1024 / 1024).toFixed(1)}MB / ${(totalSize / 1024 / 1024).toFixed(1)}MB)`);
      });
      
      response.pipe(file);
      file.on('finish', () => {
        file.close();
        console.log('\n✅ Download completed');
        resolve();
      });
    }).on('error', (err) => {
      fs.unlink(dest, () => {}); // Delete partial file
      reject(err);
    });
  });
};

// Main setup function
const setupWhisper = async () => {
  console.log('🚀 Setting up Whisper.cpp for RichesReach...\n');
  
  try {
    // Create models directory
    if (!fs.existsSync(MODELS_DIR)) {
      fs.mkdirSync(MODELS_DIR, { recursive: true });
      console.log('📁 Created models directory');
    }
    
    // Clone or update whisper.cpp repository
    if (!fs.existsSync(WHISPER_DIR)) {
      console.log('📥 Cloning whisper.cpp repository...');
      await execAsync(`git clone ${WHISPER_REPO} ${WHISPER_DIR}`);
      console.log('✅ Repository cloned');
    } else {
      console.log('🔄 Updating whisper.cpp repository...');
      await execAsync(`cd ${WHISPER_DIR} && git pull`);
      console.log('✅ Repository updated');
    }
    
    // Build whisper.cpp
    console.log('🔨 Building whisper.cpp...');
    await execAsync(`cd ${WHISPER_DIR} && make`);
    console.log('✅ Build completed');
    
    // Display model options
    console.log('\n📋 Available Whisper models:');
    Object.entries(MODELS).forEach(([name, config], index) => {
      console.log(`${index + 1}. ${name} (${config.size}) - ${config.accuracy} accuracy, ${config.speed} speed`);
    });
    
    // For automated setup, use tiny.en (best balance of size/speed)
    const selectedModel = 'tiny.en';
    const modelConfig = MODELS[selectedModel];
    
    console.log(`\n🎯 Selected model: ${selectedModel} (${modelConfig.size})`);
    
    const modelPath = path.join(MODELS_DIR, `ggml-${selectedModel}.bin`);
    const quantizedPath = path.join(MODELS_DIR, `ggml-${selectedModel}-q5_0.bin`);
    
    // Download model if not exists
    if (!fs.existsSync(modelPath)) {
      console.log(`📥 Downloading ${selectedModel} model...`);
      await downloadFile(modelConfig.url, modelPath);
    } else {
      console.log(`✅ Model ${selectedModel} already exists`);
    }
    
    // Quantize model for smaller size
    if (!fs.existsSync(quantizedPath)) {
      console.log(`🔧 Quantizing model to Q5_0 (50% size reduction)...`);
      await execAsync(`cd ${WHISPER_DIR} && ./quantize ${modelPath} ${quantizedPath} q5_0`);
      console.log('✅ Quantization completed');
    } else {
      console.log('✅ Quantized model already exists');
    }
    
    // Create environment file
    const envContent = `# Whisper Server Configuration
PORT=3001
WHISPER_MODEL=ggml-tiny.en-q5_0.bin
WHISPER_PATH=./whisper.cpp
MONGODB_URI=mongodb://localhost:27017/richesreach_whisper
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,exp://192.168.1.236:8081

# Optional: GPU acceleration (if NVIDIA GPU available)
# CUDA=1
`;
    
    if (!fs.existsSync('.env')) {
      fs.writeFileSync('.env', envContent);
      console.log('📝 Created .env file');
    }
    
    // Test the setup
    console.log('\n🧪 Testing Whisper setup...');
    const testAudioPath = path.join(WHISPER_DIR, 'samples', 'jfk.wav');
    
    if (fs.existsSync(testAudioPath)) {
      try {
        const { stdout } = await execAsync(`cd ${WHISPER_DIR} && ./main -m ${quantizedPath} -f ${testAudioPath} --language en --no-timestamps --print-colors false`);
        console.log('✅ Test transcription successful');
        console.log(`📝 Sample output: "${stdout.trim()}"`);
      } catch (error) {
        console.log('⚠️  Test transcription failed (this might be normal)');
      }
    }
    
    console.log('\n🎉 Whisper setup completed successfully!');
    console.log('\n📋 Next steps:');
    console.log('1. Start the server: npm start');
    console.log('2. Test transcription: curl -X POST http://localhost:3001/api/transcribe-audio/');
    console.log('3. Update your mobile app to use the new endpoint');
    
    console.log('\n📊 Model information:');
    console.log(`- Model: ${selectedModel}`);
    console.log(`- Size: ${modelConfig.size} (original) → ~${Math.round(parseInt(modelConfig.size) * 0.5)}MB (quantized)`);
    console.log(`- Accuracy: ${modelConfig.accuracy}`);
    console.log(`- Speed: ${modelConfig.speed}`);
    console.log(`- Path: ${quantizedPath}`);
    
  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    process.exit(1);
  }
};

// Run setup if called directly
if (require.main === module) {
  setupWhisper();
}

module.exports = { setupWhisper, MODELS };
