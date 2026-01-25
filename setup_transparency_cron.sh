#!/bin/bash
# Setup cron job for FSS v3.0 Weekly Transparency Report
# This script sets up automatic weekly PDF report generation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"
PYTHON_SCRIPT="$SCRIPT_DIR/fss_transparency_engine.py"

echo "=========================================="
echo "FSS v3.0 Transparency Engine - Cron Setup"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "⚠️  Virtual environment not found at: $VENV_PATH"
    echo "   Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    echo "✅ Virtual environment created"
fi

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Error: fss_transparency_engine.py not found at: $PYTHON_SCRIPT"
    exit 1
fi

# Make script executable
chmod +x "$PYTHON_SCRIPT"

# Create reports directory
mkdir -p "$SCRIPT_DIR/reports"
echo "✅ Reports directory ready: $SCRIPT_DIR/reports"

# Create cron job entry
CRON_ENTRY="0 9 * * 1 cd $SCRIPT_DIR && source $VENV_PATH/bin/activate && python $PYTHON_SCRIPT >> $SCRIPT_DIR/reports/cron.log 2>&1"

echo ""
echo "Cron job entry to add:"
echo "----------------------------------------"
echo "$CRON_ENTRY"
echo "----------------------------------------"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "fss_transparency_engine.py"; then
    echo "⚠️  Cron job already exists for fss_transparency_engine.py"
    echo ""
    echo "Current crontab:"
    crontab -l | grep "fss_transparency_engine.py"
    echo ""
    read -p "Do you want to replace it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove old entry
        crontab -l 2>/dev/null | grep -v "fss_transparency_engine.py" | crontab -
        # Add new entry
        (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
        echo "✅ Cron job updated"
    else
        echo "ℹ️  Keeping existing cron job"
    fi
else
    # Add new cron job
    read -p "Do you want to add this cron job now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
        echo "✅ Cron job added successfully!"
        echo ""
        echo "The transparency report will run every Monday at 9:00 AM"
    else
        echo "ℹ️  To add manually, run:"
        echo "   crontab -e"
        echo "   Then add this line:"
        echo "   $CRON_ENTRY"
    fi
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To view your cron jobs:"
echo "   crontab -l"
echo ""
echo "To edit cron jobs:"
echo "   crontab -e"
echo ""
echo "To test the script manually:"
echo "   cd $SCRIPT_DIR && source $VENV_PATH/bin/activate && python $PYTHON_SCRIPT"
echo ""
echo "Reports will be saved to:"
echo "   $SCRIPT_DIR/reports/"
echo ""

