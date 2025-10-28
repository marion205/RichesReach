#!/bin/bash

# RichesReach AI Demo Recording Script
# Automates demo recordings for YC/Techstars pitches

set -e

echo "🎬 Starting RichesReach AI Demo Recording..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEMO_DIR="./demo-recordings"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PLATFORM=${1:-ios} # ios or android

echo -e "${BLUE}📱 Platform: $PLATFORM${NC}"
echo -e "${BLUE}📁 Demo Directory: $DEMO_DIR${NC}"

# Create demo directory
mkdir -p $DEMO_DIR

# Function to run demo test
run_demo_test() {
    local test_name=$1
    local test_file=$2
    local output_name=$3
    
    echo -e "${YELLOW}🎯 Running $test_name Demo...${NC}"
    
    if [ "$PLATFORM" = "ios" ]; then
        detox test --configuration ios.sim.debug --testNamePattern="$test_name" --record-videos all --artifacts-location "$DEMO_DIR/$output_name" $test_file
    else
        detox test --configuration android.emu.debug --testNamePattern="$test_name" --record-videos all --artifacts-location "$DEMO_DIR/$output_name" $test_file
    fi
    
    echo -e "${GREEN}✅ $test_name Demo Complete${NC}"
}

# Function to create combined demo video
create_combined_demo() {
    echo -e "${YELLOW}🎬 Creating Combined Demo Video...${NC}"
    
    # List of demo videos to combine
    local videos=(
        "$DEMO_DIR/voice-trading-demo/artifacts/*.mp4"
        "$DEMO_DIR/memequest-demo/artifacts/*.mp4"
        "$DEMO_DIR/ai-coach-demo/artifacts/*.mp4"
        "$DEMO_DIR/learning-demo/artifacts/*.mp4"
        "$DEMO_DIR/social-features-demo/artifacts/*.mp4"
    )
    
    # Create video list file for ffmpeg
    echo "# RichesReach AI Demo Videos" > $DEMO_DIR/video_list.txt
    for video in "${videos[@]}"; do
        if [ -f $video ]; then
            echo "file '$video'" >> $DEMO_DIR/video_list.txt
        fi
    done
    
    # Combine videos with ffmpeg
    ffmpeg -f concat -safe 0 -i $DEMO_DIR/video_list.txt -c copy $DEMO_DIR/richesreach_complete_demo_$TIMESTAMP.mp4
    
    echo -e "${GREEN}✅ Combined Demo Video Created: richesreach_complete_demo_$TIMESTAMP.mp4${NC}"
}

# Function to add voiceover and metrics
add_voiceover_and_metrics() {
    local input_video=$1
    local output_video=$2
    
    echo -e "${YELLOW}🎤 Adding Voiceover and Metrics...${NC}"
    
    # Create metrics overlay
    cat > $DEMO_DIR/metrics_overlay.txt << EOF
68% Retention Rate
25-40% DAU Increase
50% Faster Execution
15% Better Performance
\$1.2T Market Opportunity
EOF
    
    # Add voiceover and metrics overlay
    ffmpeg -i "$input_video" \
        -vf "drawtext=text='RichesReach AI':x=10:y=10:fontsize=24:color=white:box=1:boxcolor=black@0.5" \
        -vf "drawtext=text='Voice AI Trading':x=10:y=50:fontsize=18:color=yellow:box=1:boxcolor=black@0.5" \
        -vf "drawtext=text='68% Retention':x=10:y=90:fontsize=16:color=green:box=1:boxcolor=black@0.5" \
        -c:a aac -b:a 128k "$output_video"
    
    echo -e "${GREEN}✅ Voiceover and Metrics Added${NC}"
}

# Main execution
echo -e "${BLUE}🚀 Starting Demo Recording Process...${NC}"

# Run individual demo tests
run_demo_test "Voice Trading Demo" "e2e/VoiceTradingDemo.test.js" "voice-trading-demo"
run_demo_test "MemeQuest Social Trading Demo" "e2e/VoiceTradingDemo.test.js" "memequest-demo"
run_demo_test "AI Trading Coach Demo" "e2e/VoiceTradingDemo.test.js" "ai-coach-demo"
run_demo_test "Learning System Demo" "e2e/VoiceTradingDemo.test.js" "learning-demo"
run_demo_test "Wealth Circles Community Demo" "e2e/SocialFeaturesDemo.test.js" "social-features-demo"

# Create combined demo
create_combined_demo

# Add voiceover and metrics
add_voiceover_and_metrics "$DEMO_DIR/richesreach_complete_demo_$TIMESTAMP.mp4" "$DEMO_DIR/richesreach_final_demo_$TIMESTAMP.mp4"

echo -e "${GREEN}🎉 Demo Recording Complete!${NC}"
echo -e "${BLUE}📁 Output: $DEMO_DIR/richesreach_final_demo_$TIMESTAMP.mp4${NC}"
echo -e "${YELLOW}💡 Ready for YC/Techstars submission!${NC}"

# Optional: Upload to cloud storage
if [ "$2" = "upload" ]; then
    echo -e "${YELLOW}☁️ Uploading to cloud storage...${NC}"
    # Add your cloud upload logic here (AWS S3, Google Drive, etc.)
fi
