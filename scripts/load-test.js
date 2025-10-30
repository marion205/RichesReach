#!/usr/bin/env node

/**
 * RichesReach Live Streaming Load Testing Script
 * 
 * This script simulates multiple concurrent users joining live streams,
 * sending messages, reactions, and participating in polls to test
 * system performance and scalability.
 * 
 * Usage:
 *   node scripts/load-test.js [options]
 * 
 * Options:
 *   --viewers <number>    Number of concurrent viewers (default: 50)
 *   --duration <minutes>  Test duration in minutes (default: 10)
 *   --base-url <url>      API base URL (default: http://process.env.EXPO_PUBLIC_API_HOST || "localhost":8000)
 *   --token <token>       Authentication token
 *   --verbose             Enable verbose logging
 *   --help                Show help message
 */

const fetch = require('node-fetch');
const WebSocket = require('ws');
const readline = require('readline');

// Configuration
const config = {
  viewers: 50,
  duration: 10, // minutes
  baseUrl: 'http://process.env.EXPO_PUBLIC_API_HOST || "localhost":8000',
  token: 'test-token',
  verbose: false,
  messageInterval: 5000, // 5 seconds
  reactionInterval: 3000, // 3 seconds
  pollInterval: 30000, // 30 seconds
};

// Statistics tracking
const stats = {
  streamsCreated: 0,
  streamsStarted: 0,
  viewersJoined: 0,
  messagesSent: 0,
  reactionsSent: 0,
  pollsCreated: 0,
  votesCast: 0,
  errors: 0,
  startTime: null,
  endTime: null,
};

// Active viewers and streams
const activeViewers = new Map();
const activeStreams = new Map();

// Parse command line arguments
function parseArgs() {
  const args = process.argv.slice(2);
  
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--viewers':
        config.viewers = parseInt(args[++i]) || 50;
        break;
      case '--duration':
        config.duration = parseInt(args[++i]) || 10;
        break;
      case '--base-url':
        config.baseUrl = args[++i] || 'http://process.env.EXPO_PUBLIC_API_HOST || "localhost":8000';
        break;
      case '--token':
        config.token = args[++i] || 'test-token';
        break;
      case '--verbose':
        config.verbose = true;
        break;
      case '--help':
        showHelp();
        process.exit(0);
        break;
    }
  }
}

function showHelp() {
  console.log(`
RichesReach Live Streaming Load Testing Script

Usage: node scripts/load-test.js [options]

Options:
  --viewers <number>    Number of concurrent viewers (default: 50)
  --duration <minutes>  Test duration in minutes (default: 10)
  --base-url <url>      API base URL (default: http://process.env.EXPO_PUBLIC_API_HOST || "localhost":8000)
  --token <token>       Authentication token
  --verbose             Enable verbose logging
  --help                Show help message

Examples:
  node scripts/load-test.js --viewers 100 --duration 15
  node scripts/load-test.js --base-url http://process.env.API_BASE_URL || "localhost:8000" --token my-token
  node scripts/load-test.js --verbose
`);
}

// Utility functions
function log(message, level = 'info') {
  const timestamp = new Date().toISOString();
  const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
  
  if (level === 'error' || config.verbose) {
    console.log(`${prefix} ${message}`);
  }
}

function logStats() {
  const duration = (Date.now() - stats.startTime) / 1000;
  const rate = {
    messagesPerSecond: (stats.messagesSent / duration).toFixed(2),
    reactionsPerSecond: (stats.reactionsSent / duration).toFixed(2),
    errorsPerSecond: (stats.errors / duration).toFixed(2),
  };
  
  console.log('\n📊 Load Test Statistics:');
  console.log(`⏱️  Duration: ${(duration / 60).toFixed(2)} minutes`);
  console.log(`👥 Viewers: ${stats.viewersJoined}`);
  console.log(`📺 Streams: ${stats.streamsStarted}`);
  console.log(`💬 Messages: ${stats.messagesSent} (${rate.messagesPerSecond}/s)`);
  console.log(`🎭 Reactions: ${stats.reactionsSent} (${rate.reactionsPerSecond}/s)`);
  console.log(`📊 Polls: ${stats.pollsCreated}`);
  console.log(`🗳️  Votes: ${stats.votesCast}`);
  console.log(`❌ Errors: ${stats.errors} (${rate.errorsPerSecond}/s)`);
  console.log(`📈 Success Rate: ${((stats.messagesSent + stats.reactionsSent) / (stats.messagesSent + stats.reactionsSent + stats.errors) * 100).toFixed(2)}%`);
}

// API helper functions
async function apiRequest(endpoint, options = {}) {
  const url = `${config.baseUrl}/api${endpoint}`;
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${config.token}`,
    },
  };
  
  const requestOptions = { ...defaultOptions, ...options };
  
  try {
    const response = await fetch(url, requestOptions);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} - ${data.error || 'Unknown error'}`);
    }
    
    return data;
  } catch (error) {
    stats.errors++;
    log(`API Request failed: ${error.message}`, 'error');
    throw error;
  }
}

// Stream management
async function createStream() {
  try {
    const data = await apiRequest('/live-streams/', {
      method: 'POST',
      body: JSON.stringify({
        title: `Load Test Stream ${Date.now()}`,
        description: 'Automated load testing stream',
        circle_id: 1,
        category: 'general',
        is_public: true,
        allow_chat: true,
        allow_reactions: true,
        allow_screen_share: true,
      }),
    });
    
    stats.streamsCreated++;
    log(`Created stream: ${data.data.id}`, 'info');
    return data.data;
  } catch (error) {
    log(`Failed to create stream: ${error.message}`, 'error');
    throw error;
  }
}

async function startStream(streamId) {
  try {
    const data = await apiRequest(`/live-streams/${streamId}/start/`, {
      method: 'POST',
    });
    
    stats.streamsStarted++;
    log(`Started stream: ${streamId}`, 'info');
    return data.data;
  } catch (error) {
    log(`Failed to start stream: ${error.message}`, 'error');
    throw error;
  }
}

async function endStream(streamId) {
  try {
    const data = await apiRequest(`/live-streams/${streamId}/end/`, {
      method: 'POST',
    });
    
    log(`Ended stream: ${streamId}`, 'info');
    return data.data;
  } catch (error) {
    log(`Failed to end stream: ${error.message}`, 'error');
    throw error;
  }
}

// Viewer simulation
class Viewer {
  constructor(id, streamId) {
    this.id = id;
    this.streamId = streamId;
    this.joined = false;
    this.messageInterval = null;
    this.reactionInterval = null;
    this.pollInterval = null;
  }
  
  async join() {
    try {
      await apiRequest(`/live-streams/${this.streamId}/join/`, {
        method: 'POST',
      });
      
      this.joined = true;
      stats.viewersJoined++;
      log(`Viewer ${this.id} joined stream ${this.streamId}`, 'info');
      
      // Start sending messages
      this.startMessaging();
      
      // Start sending reactions
      this.startReactions();
      
      // Start creating polls (only for some viewers)
      if (this.id % 10 === 0) {
        this.startPolling();
      }
      
    } catch (error) {
      log(`Viewer ${this.id} failed to join: ${error.message}`, 'error');
      throw error;
    }
  }
  
  async leave() {
    try {
      if (this.joined) {
        await apiRequest(`/live-streams/${this.streamId}/leave/`, {
          method: 'POST',
        });
        
        this.joined = false;
        log(`Viewer ${this.id} left stream ${this.streamId}`, 'info');
      }
      
      // Clear intervals
      if (this.messageInterval) clearInterval(this.messageInterval);
      if (this.reactionInterval) clearInterval(this.reactionInterval);
      if (this.pollInterval) clearInterval(this.pollInterval);
      
    } catch (error) {
      log(`Viewer ${this.id} failed to leave: ${error.message}`, 'error');
    }
  }
  
  startMessaging() {
    this.messageInterval = setInterval(async () => {
      try {
        const messages = [
          `Hello from viewer ${this.id}!`,
          `Great stream!`,
          `What do you think about the market?`,
          `Thanks for the insights!`,
          `This is very helpful!`,
          `Can you explain more about that?`,
          `I agree with your analysis`,
          `What's your next move?`,
          `Excellent presentation!`,
          `Keep up the great work!`,
        ];
        
        const message = messages[Math.floor(Math.random() * messages.length)];
        
        await apiRequest(`/live-streams/${this.streamId}/messages/send/`, {
          method: 'POST',
          body: JSON.stringify({
            content: message,
            message_type: 'message',
          }),
        });
        
        stats.messagesSent++;
        log(`Viewer ${this.id} sent message: ${message}`, 'info');
        
      } catch (error) {
        log(`Viewer ${this.id} failed to send message: ${error.message}`, 'error');
      }
    }, config.messageInterval + Math.random() * 2000); // Add some randomness
  }
  
  startReactions() {
    this.reactionInterval = setInterval(async () => {
      try {
        const reactions = ['heart', 'fire', 'money', 'thumbs', 'clap', 'laugh'];
        const reaction = reactions[Math.floor(Math.random() * reactions.length)];
        
        await apiRequest(`/live-streams/${this.streamId}/reactions/send/`, {
          method: 'POST',
          body: JSON.stringify({
            reaction_type: reaction,
          }),
        });
        
        stats.reactionsSent++;
        log(`Viewer ${this.id} sent reaction: ${reaction}`, 'info');
        
      } catch (error) {
        log(`Viewer ${this.id} failed to send reaction: ${error.message}`, 'error');
      }
    }, config.reactionInterval + Math.random() * 1000); // Add some randomness
  }
  
  startPolling() {
    this.pollInterval = setInterval(async () => {
      try {
        const pollQuestions = [
          {
            question: "What's your biggest investment challenge?",
            options: ["Market volatility", "Lack of knowledge", "Emotional decisions", "Time management"]
          },
          {
            question: "How often do you check your portfolio?",
            options: ["Daily", "Weekly", "Monthly", "Rarely"]
          },
          {
            question: "What's your risk tolerance?",
            options: ["Conservative", "Moderate", "Aggressive", "Very Aggressive"]
          },
          {
            question: "Which asset class interests you most?",
            options: ["Stocks", "Bonds", "Real Estate", "Crypto"]
          }
        ];
        
        const poll = pollQuestions[Math.floor(Math.random() * pollQuestions.length)];
        
        const pollData = await apiRequest(`/live-streams/${this.streamId}/polls/create/`, {
          method: 'POST',
          body: JSON.stringify({
            question: poll.question,
            options: poll.options,
            is_multiple_choice: false,
            expires_in: 10,
          }),
        });
        
        stats.pollsCreated++;
        log(`Viewer ${this.id} created poll: ${poll.question}`, 'info');
        
        // Simulate voting on the poll
        setTimeout(async () => {
          try {
            const polls = await apiRequest(`/live-streams/${this.streamId}/polls/`);
            if (polls.data.length > 0) {
              const activePoll = polls.data[0];
              if (activePoll.options.length > 0) {
                const randomOption = activePoll.options[Math.floor(Math.random() * activePoll.options.length)];
                
                await apiRequest(`/live-streams/${this.streamId}/polls/${activePoll.id}/vote/`, {
                  method: 'POST',
                  body: JSON.stringify({
                    option_ids: [randomOption.id],
                  }),
                });
                
                stats.votesCast++;
                log(`Viewer ${this.id} voted on poll: ${randomOption.text}`, 'info');
              }
            }
          } catch (error) {
            log(`Viewer ${this.id} failed to vote: ${error.message}`, 'error');
          }
        }, 2000);
        
      } catch (error) {
        log(`Viewer ${this.id} failed to create poll: ${error.message}`, 'error');
      }
    }, config.pollInterval + Math.random() * 10000); // Add some randomness
  }
}

// Main load testing function
async function runLoadTest() {
  console.log('🚀 Starting RichesReach Live Streaming Load Test');
  console.log(`📊 Configuration:`);
  console.log(`   Viewers: ${config.viewers}`);
  console.log(`   Duration: ${config.duration} minutes`);
  console.log(`   Base URL: ${config.baseUrl}`);
  console.log(`   Verbose: ${config.verbose}`);
  console.log('');
  
  stats.startTime = Date.now();
  
  try {
    // Create and start a stream
    log('Creating test stream...', 'info');
    const stream = await createStream();
    const startedStream = await startStream(stream.id);
    
    activeStreams.set(stream.id, {
      stream: startedStream,
      viewers: new Set(),
    });
    
    // Create and join viewers
    log(`Creating ${config.viewers} viewers...`, 'info');
    const viewerPromises = [];
    
    for (let i = 0; i < config.viewers; i++) {
      const viewer = new Viewer(i, stream.id);
      activeViewers.set(i, viewer);
      
      // Stagger viewer joins to simulate real-world behavior
      const delay = Math.random() * 5000; // 0-5 seconds
      
      viewerPromises.push(
        new Promise(resolve => {
          setTimeout(async () => {
            try {
              await viewer.join();
              activeStreams.get(stream.id).viewers.add(i);
              resolve();
            } catch (error) {
              resolve(); // Continue even if some viewers fail
            }
          }, delay);
        })
      );
    }
    
    // Wait for all viewers to join
    await Promise.all(viewerPromises);
    
    log(`Load test running with ${stats.viewersJoined} active viewers`, 'info');
    log(`Press Ctrl+C to stop the test`, 'info');
    
    // Set up periodic stats logging
    const statsInterval = setInterval(() => {
      logStats();
    }, 60000); // Every minute
    
    // Set up graceful shutdown
    process.on('SIGINT', async () => {
      console.log('\n🛑 Stopping load test...');
      clearInterval(statsInterval);
      await cleanup();
      process.exit(0);
    });
    
    // Run for specified duration
    setTimeout(async () => {
      console.log('\n⏰ Test duration completed');
      clearInterval(statsInterval);
      await cleanup();
      process.exit(0);
    }, config.duration * 60 * 1000);
    
  } catch (error) {
    log(`Load test failed: ${error.message}`, 'error');
    await cleanup();
    process.exit(1);
  }
}

// Cleanup function
async function cleanup() {
  stats.endTime = Date.now();
  
  log('Cleaning up...', 'info');
  
  // Disconnect all viewers
  const viewerPromises = Array.from(activeViewers.values()).map(viewer => viewer.leave());
  await Promise.all(viewerPromises);
  
  // End all streams
  const streamPromises = Array.from(activeStreams.keys()).map(streamId => endStream(streamId));
  await Promise.all(streamPromises);
  
  // Log final statistics
  logStats();
  
  log('Load test completed', 'info');
}

// Run the load test
if (require.main === module) {
  parseArgs();
  runLoadTest().catch(error => {
    console.error('Load test failed:', error);
    process.exit(1);
  });
}

module.exports = {
  runLoadTest,
  Viewer,
  config,
  stats,
};
