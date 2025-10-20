# 📱 **Mobile App Testing Guide - GenAI Features** 🚀

## 🎯 **How to Test the New GenAI Features**

### **Step 1: Open the App**
1. **Scan the QR code** with your phone's camera (iOS) or Expo Go app (Android)
2. **Or press `i`** in the terminal to open iOS simulator
3. **Or press `a`** in the terminal to open Android emulator

### **Step 2: Navigate to GenAI Features**

Once the app loads, you'll see the **Home Screen** with a new **"AI Assistant"** section at the bottom.

---

## 🧪 **Testing All GenAI Features**

### **1. AI Assistant Chat** 💬
- **Location:** Home Screen → "AI Assistant" section → "AI Assistant Chat"
- **What to test:**
  - Ask questions like "How do I start investing?"
  - Try "What is compound interest?"
  - Test "Explain dollar cost averaging"
- **Expected:** Real-time chat interface with AI responses

### **2. Tutor Ask/Explain** 🎓
- **Location:** Home Screen → "AI Assistant" section → "Tutor Ask/Explain"
- **What to test:**
  - **Ask Mode:** "What is a stock option?"
  - **Explain Mode:** "dollar cost averaging"
- **Expected:** Toggle between Ask/Explain modes, get detailed explanations

### **3. Tutor Quiz** 📝
- **Location:** Home Screen → "AI Assistant" section → "Tutor Quiz"
- **What to test:**
  - Click "Load Quiz" button
  - Answer the generated questions
  - Click "Submit Answers" to see your score
- **Expected:** Interactive quiz with scoring and explanations

### **4. Tutor Module** 📚
- **Location:** Home Screen → "AI Assistant" section → "Tutor Module"
- **What to test:**
  - Click "Generate Module" button
  - Scroll through the educational content
  - Check the quiz preview section
- **Expected:** Structured learning modules with sections and quizzes

### **5. Market Commentary** 📈
- **Location:** Home Screen → "AI Assistant" section → "Market Commentary"
- **What to test:**
  - Try different **horizons:** daily, weekly, monthly
  - Try different **tones:** neutral, bullish, bearish, educational
  - Click "Refresh" to get new commentary
- **Expected:** Market insights with drivers, sectors, risks, and opportunities

### **6. Trading Coach** 🎯
- **Location:** Home Screen → "AI Assistant" section → "Trading Coach"
- **What to test:**
  - Enter a goal like "Build wealth for retirement"
  - Select **risk tolerance:** low, medium, high
  - Select **horizon:** short, medium, long
  - Click "Get Advice" and "Get Strategies"
- **Expected:** Personalized trading guidance with risk considerations

---

## 🎨 **UI/UX Features to Notice**

### **Dark Theme Design** 🌙
- Consistent dark background (`#0b0b0f`)
- Modern card-based layouts
- Proper contrast and readability

### **Interactive Elements** ⚡
- **Segmented toggles** for mode selection
- **Loading states** with spinners
- **Error handling** with user-friendly messages
- **Confidence scores** and model information
- **Copy buttons** for easy sharing

### **Responsive Design** 📱
- **Safe area padding** for different screen sizes
- **Scrollable content** for long responses
- **Proper spacing** and typography
- **Touch-friendly** button sizes

---

## 🔧 **Backend Integration**

### **API Endpoints Being Tested:**
- `POST /tutor/ask` - AI Q&A
- `POST /tutor/explain` - Concept explanations
- `POST /tutor/quiz` - Quiz generation
- `POST /tutor/module` - Educational modules
- `POST /tutor/market-commentary` - Market insights
- `POST /assistant/query` - Conversational assistant
- `POST /coach/advise` - Trading advice
- `POST /coach/strategy` - Trading strategies

### **Expected Response Times:**
- **Quick responses:** 100-300ms
- **Complex content:** 300-600ms
- **Fallback responses:** <100ms (when APIs are unavailable)

---

## 🐛 **Troubleshooting**

### **If you see fallback responses:**
- This is normal when API credits are low
- The system gracefully handles API failures
- All endpoints still return 200 status codes

### **If the app doesn't load:**
- Check that both servers are running:
  - GenAI server on port 8124
  - Main server on port 8123
- Try reloading the app (press `r` in terminal)

### **If you see connection errors:**
- Make sure your phone and computer are on the same WiFi network
- Check that the API base URL is set correctly

---

## 🎉 **What You Should See**

### **Working Features:**
✅ All 6 GenAI screens accessible from Home Screen  
✅ Modern dark UI with consistent design  
✅ Interactive elements (toggles, buttons, forms)  
✅ Loading states and error handling  
✅ Structured content display  
✅ Real-time AI responses (or graceful fallbacks)  

### **Navigation Flow:**
1. **Home Screen** → AI Assistant section
2. **Select any GenAI feature** → Navigate to dedicated screen
3. **Interact with the feature** → Get AI-powered responses
4. **Navigate back** → Return to Home Screen

---

## 🚀 **Ready to Test!**

The mobile app is now running with all GenAI features fully integrated. You can test the complete user experience from the comfort of your phone or simulator.

**All systems are operational and ready for testing!** 🎯
