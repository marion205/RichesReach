#!/bin/bash
# Quick script to stop demo recording

echo "⏹️  Stopping demo recording..."

# Kill recording processes
pkill -f "recordVideo" 2>/dev/null
pkill -f "record-demo" 2>/dev/null
kill $(cat /tmp/demo_record_pid.txt 2>/dev/null) 2>/dev/null || true
rm -f /tmp/demo_record_pid.txt

sleep 3

# Check if stopped
if ! pgrep -f "recordVideo" > /dev/null; then
  echo "✅ Recording stopped successfully"
  
  # Find the latest recording file
  LATEST=$(ls -t ~/Desktop/RichesReach_Demo_*.mov 2>/dev/null | head -1)
  if [ -n "$LATEST" ]; then
    SIZE=$(du -h "$LATEST" 2>/dev/null | cut -f1)
    echo ""
    echo "📹 Video saved: $LATEST"
    echo "   Size: $SIZE"
    echo ""
    echo "✅ You can now open it with QuickTime Player!"
  fi
else
  echo "⚠️  Some processes may still be running"
  echo "   Try: pkill -f recordVideo"
fi

