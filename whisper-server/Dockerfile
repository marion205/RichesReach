# Multi-stage Docker build for Whisper server
FROM ubuntu:22.04 as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    python3 \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Clone and build whisper.cpp
WORKDIR /app
RUN git clone https://github.com/ggerganov/whisper.cpp.git
WORKDIR /app/whisper.cpp
RUN make

# Download and quantize model
RUN mkdir -p models
RUN wget -O models/ggml-tiny.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin
RUN ./quantize models/ggml-tiny.en.bin models/ggml-tiny.en-q5_0.bin q5_0

# Production stage
FROM ubuntu:22.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Create app directory
WORKDIR /app

# Copy built whisper.cpp
COPY --from=builder /app/whisper.cpp /app/whisper.cpp

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads models

# Set environment variables
ENV NODE_ENV=production
ENV WHISPER_MODEL=ggml-tiny.en-q5_0.bin
ENV WHISPER_PATH=/app/whisper.cpp
ENV PORT=3001

# Expose port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3001/health || exit 1

# Start the application
CMD ["npm", "start"]
