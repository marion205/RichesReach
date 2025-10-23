#!/bin/bash

# 🧪 RichesReach Manual E2E Testing Execution Script
# This script guides you through comprehensive manual testing

echo "🚀 RichesReach Manual E2E Testing - Version 2"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${PURPLE}🎯 $1${NC}"
    echo "=================================="
}

print_step() {
    echo -e "${BLUE}📱 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Expo is running
print_header "CHECKING EXPO SERVER STATUS"
if pgrep -f "expo start" > /dev/null; then
    print_success "Expo development server is running"
    print_info "You should see a QR code in your terminal"
    print_info "If not, check the terminal where you ran 'npx expo start --clear'"
else
    print_warning "Expo server not detected"
    print_info "Starting Expo server..."
    npx expo start --clear &
    sleep 5
fi

echo ""
print_header "DEVICE CONNECTION INSTRUCTIONS"
print_step "1. Open Expo Go app on your phone"
print_step "2. Scan the QR code from the terminal"
print_step "3. Wait for app to load (30-60 seconds)"
print_step "4. App should open to login screen"

echo ""
read -p "Press Enter when you have the app loaded on your device..."

echo ""
print_header "CRITICAL PATH 1: LOGIN & HOME SCREEN"
print_step "Testing Login Process"
echo "Expected:"
echo "  • 'Welcome Back' title visible"
echo "  • Demo credentials pre-filled: demo@example.com / demo123"
echo "  • 'Sign In' button enabled"
echo ""
read -p "✅ Login screen looks correct? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "Login screen verified"
else
    print_error "Login screen issue - check app loading"
    exit 1
fi

print_step "Testing Login Action"
echo "Action: Tap 'Sign In' button"
echo "Expected: Navigate to Home screen with 'Smart Wealth Suite' section"
echo ""
read -p "✅ Successfully logged in and see Home screen? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "Login successful"
else
    print_error "Login failed - check credentials or network"
    exit 1
fi

print_step "Testing Smart Wealth Suite Section"
echo "Expected:"
echo "  • 'Smart Wealth Suite' title with rocket icon 🚀"
echo "  • Section positioned ABOVE 'Learning & AI Tools'"
echo "  • Three features: Oracle Insights, Voice AI Assistant, Blockchain Integration"
echo ""
read -p "✅ Smart Wealth Suite section visible and correctly positioned? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "Smart Wealth Suite section verified"
else
    print_error "Smart Wealth Suite section issue - check positioning or visibility"
fi

echo ""
print_header "CRITICAL PATH 2: VERSION 2 FEATURES TESTING"
print_step "Testing Oracle Insights"
echo "Action: Tap 'Oracle Insights' card"
echo "Expected: Navigate to Oracle Insights screen with loading state"
echo ""
read -p "✅ Oracle Insights opens and shows loading? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "Oracle Insights working"
else
    print_warning "Oracle Insights issue - check navigation"
fi

print_step "Testing Voice AI Assistant"
echo "Action: Go back to Home, then tap 'Voice AI Assistant'"
echo "Expected: Navigate to Voice AI Assistant with microphone interface"
echo ""
read -p "✅ Voice AI Assistant opens with microphone interface? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "Voice AI Assistant working"
else
    print_warning "Voice AI Assistant issue - check interface"
fi

print_step "Testing Blockchain Integration"
echo "Action: Go back to Home, then tap 'Blockchain Integration'"
echo "Expected: Navigate to Blockchain Integration with DeFi features"
echo ""
read -p "✅ Blockchain Integration opens with DeFi features? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "Blockchain Integration working"
else
    print_warning "Blockchain Integration issue - check features"
fi

echo ""
print_header "CRITICAL PATH 3: PROFILE FEATURES"
print_step "Testing Profile Navigation"
echo "Action: Tap 'Profile' tab in bottom navigation"
echo "Expected: Navigate to Profile screen with 'Actions' section"
echo ""
read -p "✅ Profile screen opens with Actions section? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "Profile navigation working"
else
    print_error "Profile navigation issue - check bottom tabs"
fi

print_step "Testing Theme Settings"
echo "Action: In Actions section, tap 'Theme Settings'"
echo "Expected: Navigate to Theme Settings with dark mode toggle"
echo ""
read -p "✅ Theme Settings opens with dark mode toggle? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "Theme Settings working"
    print_step "Testing Dark Mode Toggle"
    echo "Action: Toggle dark mode switch"
    echo "Expected: App appearance changes to dark theme"
    echo ""
    read -p "✅ Dark mode toggle works and changes appearance? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_success "Dark mode toggle working"
    else
        print_warning "Dark mode toggle issue - check theme implementation"
    fi
else
    print_warning "Theme Settings issue - check navigation"
fi

print_step "Testing Security Fortress"
echo "Action: Go back to Profile, then tap 'Security Fortress'"
echo "Expected: Navigate to Security Fortress with security features"
echo ""
read -p "✅ Security Fortress opens with security features? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "Security Fortress working"
else
    print_warning "Security Fortress issue - check features"
fi

print_step "Testing Viral Growth System"
echo "Action: Go back to Profile, then tap 'Viral Growth System'"
echo "Expected: Navigate to Viral Growth System (NOT home screen)"
echo ""
read -p "✅ Viral Growth System opens (not home screen)? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "Viral Growth System routing fixed"
else
    print_error "Viral Growth System routing issue - goes to home screen"
fi

echo ""
print_header "CRITICAL PATH 4: PORTFOLIO FEATURES"
print_step "Testing Portfolio Navigation"
echo "Action: Tap 'Portfolio' tab in bottom navigation"
echo "Expected: Navigate to Portfolio screen with overview"
echo ""
read -p "✅ Portfolio screen opens with overview? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "Portfolio navigation working"
else
    print_error "Portfolio navigation issue - check bottom tabs"
fi

print_step "Testing Wellness Score Dashboard"
echo "Action: Look for and tap 'Wellness Score Dashboard' button/card"
echo "Expected: Modal opens full screen with wellness metrics"
echo ""
read -p "✅ Wellness Score Dashboard opens as modal? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "Wellness Score Dashboard modal working"
    print_step "Testing Wellness Scores"
    echo "Expected: All scores display as integers (no decimals)"
    echo "  • Risk Management score should be clean integer"
    echo "  • Other scores should also be integers"
    echo ""
    read -p "✅ All wellness scores display as integers (no decimals)? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_success "Wellness scores formatting correct"
    else
        print_warning "Wellness scores formatting issue - check Math.round() implementation"
    fi
    
    print_step "Testing Modal Positioning"
    echo "Expected: Modal doesn't go under bottom navigation bar"
    echo ""
    read -p "✅ Modal displays above bottom navigation (not under it)? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_success "Modal positioning correct"
    else
        print_error "Modal positioning issue - goes under navigation bar"
    fi
else
    print_warning "Wellness Score Dashboard issue - check button/card visibility"
fi

print_step "Testing AR Portfolio Preview"
echo "Action: Look for and tap 'AR Portfolio Preview' button/card"
echo "Expected: Navigate to AR Portfolio Preview interface"
echo ""
read -p "✅ AR Portfolio Preview opens with AR interface? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "AR Portfolio Preview working"
else
    print_warning "AR Portfolio Preview issue - check interface"
fi

echo ""
print_header "CRITICAL PATH 5: PERFORMANCE & STABILITY"
print_step "Testing App Stability"
echo "Expected: No crashes, freezes, or major performance issues"
echo ""
read -p "✅ App runs smoothly without crashes or freezes? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "App stability good"
else
    print_error "App stability issues - check performance"
fi

print_step "Testing Navigation Performance"
echo "Expected: Smooth transitions between screens"
echo ""
read -p "✅ Navigation is smooth and responsive? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "Navigation performance good"
else
    print_warning "Navigation performance issues - check transitions"
fi

echo ""
print_header "FINAL VALIDATION"
print_step "Complete User Journey Test"
echo "Testing: Login → Home → Smart Wealth Suite → Profile → Portfolio"
echo ""
read -p "✅ Complete user journey works smoothly? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "Complete user journey validated"
else
    print_warning "User journey issues - check navigation flow"
fi

echo ""
print_header "TEST RESULTS SUMMARY"
echo "=========================="
echo ""
print_info "Please document any issues found during testing:"
echo ""
echo "Issues Found:"
echo "1. ________________________________"
echo "2. ________________________________"
echo "3. ________________________________"
echo ""
echo "Working Features:"
echo "1. ________________________________"
echo "2. ________________________________"
echo "3. ________________________________"
echo ""
echo "Performance Notes:"
echo "- Loading time: ___________"
echo "- Smoothness: ___________"
echo "- Overall experience: ___________"
echo ""

print_header "DEPLOYMENT READINESS ASSESSMENT"
echo ""
read -p "🎯 Is the app ready for production deployment? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_success "🚀 APP IS READY FOR PRODUCTION! 🎉"
    echo ""
    print_info "Next steps:"
    echo "  • Document test results"
    echo "  • Address any minor issues found"
    echo "  • Prepare for app store submission"
    echo "  • Set up production monitoring"
else
    print_warning "⚠️  APP NEEDS ADDITIONAL WORK"
    echo ""
    print_info "Next steps:"
    echo "  • Address critical issues found"
    echo "  • Re-run testing after fixes"
    echo "  • Consider staging deployment first"
fi

echo ""
print_header "TESTING COMPLETE"
echo "====================="
print_success "Manual E2E testing session completed!"
print_info "Check the detailed checklist: MANUAL_E2E_TESTING_CHECKLIST.md"
print_info "Review the real-time guide: REAL_TIME_TESTING_GUIDE.md"
echo ""
print_info "Thank you for thorough testing! 🧪✨"
