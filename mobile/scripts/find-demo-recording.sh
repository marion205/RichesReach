#!/bin/bash

# RichesReach AI - Demo Recording Finder & Saver
# Helps locate and save the automated demo recording

echo "🎬 Looking for your automated demo recording..."

# Check if QuickTime Player has an unsaved recording
echo "🔍 Checking QuickTime Player for unsaved recording..."

# Try to save any unsaved recording in QuickTime Player
osascript -e '
tell application "QuickTime Player"
    if (count of documents) > 0 then
        repeat with doc in documents
            if not (saved of doc) then
                set docName to "RichesReach_Automated_Demo_" & (current date as string)
                save doc in (path to desktop as string) & docName & ".mov"
                return "Recording saved to Desktop as " & docName & ".mov"
            end if
        end repeat
        return "No unsaved recordings found in QuickTime Player"
    else
        return "No documents open in QuickTime Player"
    end if
end tell
'

# Check common locations for recent recordings
echo "🔍 Checking common recording locations..."

# Check Desktop for recent recordings
echo "📁 Checking Desktop..."
ls -la ~/Desktop/ | grep -i "screen\|recording\|movie" | tail -3

# Check Movies folder
echo "📁 Checking Movies folder..."
ls -la ~/Movies/ | grep -i "screen\|recording\|movie" | tail -3

# Check Downloads folder
echo "📁 Checking Downloads folder..."
ls -la ~/Downloads/ | grep -i "screen\|recording\|movie" | tail -3

# Check for files created today
echo "📁 Checking for files created today..."
find ~/Desktop ~/Movies ~/Downloads -name "*.mov" -o -name "*.mp4" -newermt "$(date '+%Y-%m-%d')" 2>/dev/null | head -5

echo ""
echo "💡 If you don't see your recording:"
echo "   1. Open QuickTime Player"
echo "   2. Check if there's an unsaved recording"
echo "   3. If yes, press Cmd+S to save it"
echo "   4. Choose Desktop as the save location"
echo ""
echo "🎬 Your automated demo should be ready for YC/Techstars submission!"
