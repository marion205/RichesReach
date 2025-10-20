# Mobile Navigation Test Guide

## GenAI Features Navigation Test

### 1. AI Assistant Section
From the Home screen, scroll to the "AI Assistant" section:

- **AI Assistant Chat** → `assistant-chat` ✅
- **Tutor Ask/Explain** → `tutor-ask-explain` ✅  
- **Tutor Quiz** → `tutor-quiz` ✅
- **Tutor Module** → `tutor-module` ✅
- **Market Commentary** → `market-commentary` ✅
- **Trading Coach** → `trading-coach` ✅

### 2. Route Verification
All routes should be defined in `App.tsx`:

```typescript
case 'assistant-chat': return <AssistantChatScreen />;
case 'tutor-ask-explain': return <TutorAskExplainScreen />;
case 'tutor-quiz': return <TutorQuizScreen />;
case 'tutor-module': return <TutorModuleScreen />;
case 'market-commentary': return <MarketCommentaryScreen />;
case 'trading-coach': return <TradingCoachScreen />;
```

### 3. Screen Features Test

#### AssistantChatScreen
- [ ] Chat interface loads
- [ ] Can type and send messages
- [ ] Shows loading state while sending
- [ ] Displays AI responses
- [ ] Handles errors gracefully

#### TutorAskExplainScreen  
- [ ] Toggle between Ask/Explain modes
- [ ] Can input questions/concepts
- [ ] Shows loading state
- [ ] Displays structured responses
- [ ] Shows confidence scores and model info

#### TutorQuizScreen
- [ ] Loads quiz questions
- [ ] Can select answers
- [ ] Submit/Regrade functionality
- [ ] Shows correct/incorrect feedback
- [ ] Displays final score

#### TutorModuleScreen
- [ ] Generates learning modules
- [ ] Shows metadata (difficulty, time)
- [ ] Displays module sections
- [ ] Shows quiz preview if available

#### MarketCommentaryScreen
- [ ] Horizon selector (daily/weekly/monthly)
- [ ] Tone selector (neutral/bullish/bearish/educational)
- [ ] Generates market commentary
- [ ] Shows structured content (drivers, sectors, risks, opportunities)

#### TradingCoachScreen
- [ ] Risk tolerance chips (low/medium/high)
- [ ] Time horizon chips (short/medium/long)
- [ ] Get Advice button
- [ ] Get Strategies button
- [ ] Shows full advice with risks, controls, next steps
- [ ] Shows strategy details with pros/cons
- [ ] Displays disclaimers

### 4. API Integration Test
Each screen should:
- [ ] Make API calls to backend
- [ ] Handle loading states
- [ ] Show error messages if API fails
- [ ] Display structured responses
- [ ] Handle timeouts gracefully

### 5. UI/UX Test
- [ ] Dark theme consistency
- [ ] Proper spacing and typography
- [ ] Loading indicators work
- [ ] Error states are clear
- [ ] Disabled states show properly
- [ ] Chip selectors work correctly
- [ ] Navigation back to home works

## Backend API Test
Run the test script to verify backend endpoints:

```bash
python test_genai_routes.py
```

Expected: All 8 endpoints should return 200 status codes.
