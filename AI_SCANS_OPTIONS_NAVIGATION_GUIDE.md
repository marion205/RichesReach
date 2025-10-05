# 🧭 AI Scans & Options Copilot Navigation Guide

## 🎯 **How to Access All AI Features**

### **1. AI Scans Screen** 📊
**Purpose**: Market intelligence scanning, playbook management, and hedge-fund grade analysis

**Navigation Paths**:
- **🏠 Home Screen**: Scroll down to "AI Tools" section → Tap "AI Scans" card
- **📱 Bottom Tab Bar**: Tap "AI Scans" tab (newly added)
- **🔗 Direct Access**: `navigateTo('ai-scans')`

**Features Available**:
- ✅ Market scanning with AI-powered analysis
- ✅ Pre-built playbooks for different strategies
- ✅ Custom scan creation and management
- ✅ Real-time market intelligence
- ✅ Hedge-fund grade scoring algorithms

---

### **2. AI Options Screen** ⚡
**Purpose**: Options strategy recommendations and advanced options analysis

**Navigation Paths**:
- **🏠 Home Screen**: Scroll down to "AI Tools" section → Tap "AI Options" card
- **🔗 Direct Access**: `navigateTo('ai-options')`

**Features Available**:
- ✅ AI-powered options recommendations
- ✅ Risk-adjusted strategy suggestions
- ✅ Portfolio-based options analysis
- ✅ Market outlook integration
- ✅ Strategy optimization tools

---

### **3. Options Copilot Screen** 🤖
**Purpose**: Advanced options analysis with Greeks calculation and risk management

**Navigation Paths**:
- **⚡ AI Options Screen**: Tap "Copilot" button (top right corner)
- **🔗 Direct Access**: `navigateTo('options-copilot')`

**Features Available**:
- ✅ Real-time options chain analysis
- ✅ Greeks calculation (Delta, Gamma, Theta, Vega)
- ✅ Risk assessment and management
- ✅ Payoff diagrams and scenario analysis
- ✅ Advanced options strategies

---

### **4. Scan Playbook Screen** 📚
**Purpose**: Detailed scan results and playbook management

**Navigation Paths**:
- **📊 AI Scans Screen**: Tap on any scan or playbook item
- **🔗 Direct Access**: `navigateTo('scan-playbook')`

**Features Available**:
- ✅ Detailed scan results and analysis
- ✅ Playbook performance metrics
- ✅ Strategy explanations and rationale
- ✅ Risk band analysis
- ✅ Alternative data integration

---

## 🚀 **Quick Access Methods**

### **From Home Screen**
1. **Scroll down** to find the "AI Tools" section
2. **Tap either**:
   - "AI Scans" card → Market intelligence
   - "AI Options" card → Options strategies

### **From Bottom Tab Bar**
1. **Tap "AI Scans"** tab for direct access to market scanning

### **From AI Options Screen**
1. **Tap "Copilot"** button (top right) for advanced options analysis

### **From AI Scans Screen**
1. **Tap any scan/playbook** for detailed analysis

---

## 🎨 **UI Features & Navigation**

### **Screen Headers**
- **Back Button**: Returns to previous screen
- **Title**: Shows current screen name
- **Action Buttons**: Context-specific actions (refresh, create, etc.)

### **Tab Navigation**
- **AI Scans**: Switch between "My Scans" and "Playbooks"
- **Options Copilot**: Access different analysis tools

### **Modal Dialogs**
- **Create Scan**: Build custom market scans
- **Scan Details**: View comprehensive analysis
- **Settings**: Configure preferences

---

## 🔧 **Technical Implementation**

### **Navigation Structure**
```
Home Screen
├── AI Tools Section
│   ├── AI Scans Card → ai-scans
│   └── AI Options Card → ai-options
│
Bottom Tab Bar
└── AI Scans Tab → ai-scans
│
AI Options Screen
└── Copilot Button → options-copilot
│
AI Scans Screen
└── Scan/Playbook Item → scan-playbook
```

### **Screen IDs**
- `ai-scans`: AI Scans main screen
- `ai-options`: AI Options main screen  
- `options-copilot`: Options Copilot screen
- `scan-playbook`: Scan details screen

### **Navigation Function**
```typescript
const navigateTo = (screen: string) => {
  setCurrentScreen(screen);
};
```

---

## ✅ **Verification Checklist**

**All screens are accessible via**:
- [x] Home screen AI Tools section
- [x] Bottom tab bar (AI Scans)
- [x] Direct navigation from related screens
- [x] Proper back navigation
- [x] Header titles and actions
- [x] Modal dialogs and overlays

**All features are working**:
- [x] GraphQL queries and data loading
- [x] API endpoints and backend integration
- [x] TypeScript types and interfaces
- [x] Error handling and loading states
- [x] Real-time data updates
- [x] User interactions and feedback

---

## 🎉 **Ready to Use!**

Your AI Scans and Options Copilot features are now fully accessible and integrated into the app navigation. Users can easily discover and access these powerful hedge-fund grade tools through multiple intuitive paths.

**Start exploring**: Open the app → Scroll to "AI Tools" → Tap "AI Scans" or "AI Options" to begin!
