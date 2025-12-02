#!/bin/bash
# Setup Pre-Market Scanner Cron Job
# This script helps you set up the cron job for daily pre-market scanning

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CRON_SCRIPT="$SCRIPT_DIR/schedule_pre_market_scanner.sh"

echo "🔧 Setting up Pre-Market Scanner Cron Job"
echo ""

# Make script executable
chmod +x "$CRON_SCRIPT"

echo "📝 Add this line to your crontab (crontab -e):"
echo ""
echo "# Pre-Market Scanner - Runs daily at 8:00 AM ET (13:00 UTC)"
echo "# Note: Adjust time for DST (12:00 UTC during DST)"
echo "0 13 * * 1-5 $CRON_SCRIPT"
echo ""
echo "Or run this command to add it automatically:"
echo "  (crontab -l 2>/dev/null; echo '0 13 * * 1-5 $CRON_SCRIPT') | crontab -"
echo ""
echo "📧 Don't forget to set these environment variables:"
echo "   - ALERT_EMAIL: Your email address"
echo "   - SMTP_USER: SMTP username"
echo "   - SMTP_PASSWORD: SMTP password"
echo "   - SMTP_SERVER: SMTP server (default: smtp.gmail.com)"
echo "   - SMTP_PORT: SMTP port (default: 587)"
echo "   - PUSH_NOTIFICATION_KEY: Push notification API key (optional)"
echo ""

