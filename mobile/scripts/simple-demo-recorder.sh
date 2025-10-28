#!/bin/bash

# RichesReach AI Simple Demo Recording Script
# Alternative approach using Expo and manual recording

set -e

echo "🎬 Starting RichesReach AI Demo Recording (Simple Mode)..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEMO_DIR="./demo-recordings"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${BLUE}📁 Demo Directory: $DEMO_DIR${NC}"

# Create demo directory
mkdir -p $DEMO_DIR

# Function to create demo script
create_demo_script() {
    local script_name=$1
    local description=$2
    
    cat > "$DEMO_DIR/$script_name.md" << EOF
# $description Demo Script

## Pre-Recording Setup
1. Open RichesReach app in Expo Go
2. Start screen recording (iOS: Control Center > Screen Recording)
3. Follow the steps below

## Demo Steps

### Voice AI Trading Demo
1. **Navigate to Voice AI** (2s)
   - Tap Voice AI tab
   - Show "Voice AI Assistant" screen

2. **Select Voice** (3s)
   - Tap "Nova" voice option
   - Show voice orb animation

3. **Voice Command** (5s)
   - Tap voice orb
   - Say: "Buy 100 AAPL at limit 150"
   - Show confidence: 95%

4. **Execute Trade** (3s)
   - Tap "Execute Trade"
   - Show "Trade Executed!" message

5. **Portfolio Update** (2s)
   - Tap "View Portfolio"
   - Show updated portfolio value

**Total Duration: 15 seconds**

### MemeQuest Social Trading Demo
1. **Navigate to MemeQuest** (2s)
   - Tap MemeQuest tab
   - Show "MemeQuest Raid!" screen

2. **Pick Template** (3s)
   - Tap "Frog" template
   - Show AR preview

3. **Voice Launch** (4s)
   - Tap voice orb
   - Say: "Launch Meme!"
   - Show animation

4. **AR & Confetti** (5s)
   - Tap "Animate!"
   - Tap "Send Tip!"
   - Show confetti burst

5. **Success** (3s)
   - Show "Meme Mooned!"
   - Show streak: "8 Days"

**Total Duration: 17 seconds**

### AI Trading Coach Demo
1. **Navigate to Coach** (2s)
   - Tap Coach tab
   - Show "AI Trading Coach" screen

2. **Risk Slider** (3s)
   - Drag risk slider right
   - Show "Risk Level: High"

3. **Strategy Selection** (3s)
   - Tap "Bullish Spread"
   - Show "Strategy Selected"

4. **Execute** (2s)
   - Tap execute button
   - Show "Trade Executed"

**Total Duration: 10 seconds**

### Learning System Demo
1. **Navigate to Learning** (2s)
   - Tap Learning tab
   - Show "Learning Dashboard"

2. **Start Quiz** (3s)
   - Tap "Options Quiz"
   - Show "Question 1 of 5"

3. **Answer Questions** (8s)
   - Answer: "Call Option"
   - Tap "Next"
   - Answer: "Put Option"
   - Tap "Next"

4. **Results** (4s)
   - Show "Quiz Complete!"
   - Show "+50 XP"
   - Show "Level Up!"

**Total Duration: 17 seconds**

### Social Features Demo
1. **Navigate to Community** (2s)
   - Tap Community tab
   - Show "Wealth Circles"

2. **Join League** (3s)
   - Tap "BIPOC Wealth Builders"
   - Show league details

3. **Discussion** (4s)
   - Tap "Join Discussion"
   - Type: "Great insights!"
   - Tap "Send"

4. **Engagement** (3s)
   - Show "Message Sent"
   - Show "+10 Community Points"

**Total Duration: 12 seconds**

## Post-Recording
1. Stop screen recording
2. Save video to $DEMO_DIR/
3. Edit with iMovie/CapCut
4. Add voiceover and metrics overlay

## Key Metrics to Highlight
- 68% Retention Rate
- 25-40% DAU Increase
- 50% Faster Execution
- 15% Better Performance
- \$1.2T Market Opportunity

EOF

    echo -e "${GREEN}✅ Created $script_name.md${NC}"
}

# Function to create video editing guide
create_editing_guide() {
    cat > "$DEMO_DIR/video_editing_guide.md" << EOF
# Video Editing Guide for RichesReach Demo

## Software Options
- **iMovie** (Free, macOS)
- **CapCut** (Free, mobile/desktop)
- **DaVinci Resolve** (Free, professional)
- **Final Cut Pro** (Paid, professional)

## Editing Steps

### 1. Import and Trim
- Import all demo recordings
- Trim to exact durations (see scripts)
- Remove loading screens and delays
- Total target: 60-90 seconds

### 2. Add Voiceover
- Record professional narration
- Key phrases:
  - "Introducing RichesReach AI"
  - "Voice-controlled trading"
  - "AI-powered insights"
  - "Social trading community"
  - "Gamified learning"

### 3. Add Metrics Overlay
- 68% Retention Rate
- 25-40% DAU Increase
- 50% Faster Execution
- 15% Better Performance
- \$1.2T Market Opportunity

### 4. Add Branding
- RichesReach logo
- Consistent color scheme
- Professional transitions

### 5. Export Settings
- Format: MP4
- Resolution: 1080x1920 (9:16)
- Frame Rate: 60fps
- Quality: High

## Upload Targets
- YouTube (unlisted for YC/Techstars)
- Vimeo (high quality)
- Cloud storage for sharing

EOF

    echo -e "${GREEN}✅ Created video_editing_guide.md${NC}"
}

# Function to create quick demo checklist
create_checklist() {
    cat > "$DEMO_DIR/demo_checklist.md" << EOF
# RichesReach Demo Checklist

## Pre-Recording
- [ ] App updated to latest version
- [ ] All features working properly
- [ ] Screen recording enabled
- [ ] Good lighting and audio
- [ ] Phone in portrait mode

## During Recording
- [ ] Smooth navigation between screens
- [ ] Clear voice commands
- [ ] Show key metrics and animations
- [ ] Demonstrate unique features
- [ ] Keep total time under 2 minutes

## Post-Recording
- [ ] Review video quality
- [ ] Edit out unnecessary parts
- [ ] Add professional voiceover
- [ ] Include key metrics overlay
- [ ] Export in correct format
- [ ] Upload to sharing platform

## Key Features to Highlight
- [ ] Voice AI Trading (6 voices)
- [ ] Real-time market data (<50ms)
- [ ] AI-powered analysis
- [ ] Social trading community
- [ ] Gamified learning system
- [ ] BIPOC-focused content
- [ ] Mobile-first design

## Success Metrics
- [ ] Video length: 60-90 seconds
- [ ] Quality: 1080p, 60fps
- [ ] Engagement: Clear value prop
- [ ] Professional: Polished presentation

EOF

    echo -e "${GREEN}✅ Created demo_checklist.md${NC}"
}

# Main execution
echo -e "${BLUE}🚀 Creating Demo Recording Resources...${NC}"

# Create demo scripts
create_demo_script "voice_trading_demo" "Voice AI Trading"
create_demo_script "memequest_demo" "MemeQuest Social Trading"
create_demo_script "ai_coach_demo" "AI Trading Coach"
create_demo_script "learning_demo" "Learning System"
create_demo_script "social_demo" "Social Features"

# Create guides
create_editing_guide
create_checklist

echo -e "${GREEN}🎉 Demo Recording Resources Created!${NC}"
echo -e "${BLUE}📁 All files saved to: $DEMO_DIR/${NC}"
echo -e "${YELLOW}💡 Next steps:${NC}"
echo -e "   1. Open RichesReach app in Expo Go"
echo -e "   2. Start screen recording"
echo -e "   3. Follow the demo scripts in $DEMO_DIR/"
echo -e "   4. Edit using the video editing guide"
echo -e "   5. Upload for YC/Techstars submission"

echo -e "${GREEN}🚀 Ready to create amazing demos!${NC}"
