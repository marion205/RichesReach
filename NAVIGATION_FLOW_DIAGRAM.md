# 🗺️ AI Scans & Options Copilot Navigation Flow

## 📱 **Main Navigation Flow**

```
🏠 HOME SCREEN
├── 📊 AI Tools Section
│   ├── 🔍 AI Scans Card ──────────┐
│   │                              │
│   └── ⚡ AI Options Card ────────┤
│                                  │
├── 📱 Bottom Tab Bar              │
│   └── 🔍 AI Scans Tab ──────────┘
│
└── 💬 Chat Assistant
    └── Can suggest AI features
```

## 🔍 **AI Scans Navigation**

```
📊 AI SCANS SCREEN
├── 📋 My Scans Tab
│   ├── 🔍 Scan Item ──────────────┐
│   │                              │
│   └── ➕ Create New Scan         │
│                                  │
├── 📚 Playbooks Tab               │
│   ├── 📖 Playbook Item ─────────┘
│   │
│   └── 📋 Clone Playbook
│
└── ⚙️ Settings & Filters
```

## ⚡ **AI Options Navigation**

```
⚡ AI OPTIONS SCREEN
├── 🎯 Strategy Recommendations
│   ├── 📊 Risk-Adjusted Strategies
│   ├── 💰 Portfolio-Based Analysis
│   └── 📈 Market Outlook Integration
│
├── 🤖 Copilot Button ────────────┐
│                                  │
└── ⚙️ Settings & Preferences      │
```

## 🤖 **Options Copilot Navigation**

```
🤖 OPTIONS COPILOT SCREEN
├── 📊 Options Chain Analysis
│   ├── 📈 Calls Analysis
│   ├── 📉 Puts Analysis
│   └── 📊 Greeks Calculation
│
├── 🎯 Strategy Recommendations
│   ├── 💰 Payoff Diagrams
│   ├── ⚠️ Risk Assessment
│   └── 📊 Scenario Analysis
│
└── 🔧 Advanced Tools
    ├── 📈 Volatility Analysis
    ├── 🎯 Greeks Calculator
    └── 📊 Backtesting
```

## 📚 **Scan Playbook Navigation**

```
📚 SCAN PLAYBOOK SCREEN
├── 📊 Scan Results
│   ├── 🎯 Performance Metrics
│   ├── 📈 Analysis Details
│   └── 🔍 Market Intelligence
│
├── 📖 Playbook Details
│   ├── 📋 Strategy Explanation
│   ├── ⚠️ Risk Bands
│   └── 🔗 Alt Data Hooks
│
└── ⚙️ Management
    ├── ✏️ Edit Playbook
    ├── 📋 Clone Playbook
    └── 🗑️ Delete Playbook
```

## 🔄 **Navigation Patterns**

### **Forward Navigation**
```
Home → AI Tools → AI Scans → Scan Details
Home → AI Tools → AI Options → Options Copilot
Bottom Tab → AI Scans → Playbook Details
```

### **Back Navigation**
```
Scan Details → AI Scans → Home
Options Copilot → AI Options → Home
Playbook Details → AI Scans → Home
```

### **Cross-Navigation**
```
AI Scans ←→ AI Options (via Home)
Options Copilot ←→ AI Options (direct)
Scan Details ←→ Playbook Details (via AI Scans)
```

## 🎯 **Quick Access Summary**

| Feature | Primary Path | Secondary Path | Direct Access |
|---------|-------------|----------------|---------------|
| **AI Scans** | Home → AI Tools | Bottom Tab | `navigateTo('ai-scans')` |
| **AI Options** | Home → AI Tools | - | `navigateTo('ai-options')` |
| **Options Copilot** | AI Options → Copilot | - | `navigateTo('options-copilot')` |
| **Scan Details** | AI Scans → Select | - | `navigateTo('scan-playbook')` |

## 🚀 **User Journey Examples**

### **New User Discovery**
1. **Open App** → Home Screen
2. **Scroll Down** → See "AI Tools" section
3. **Tap "AI Scans"** → Explore market scanning
4. **Tap "AI Options"** → Learn options strategies

### **Power User Workflow**
1. **Bottom Tab** → "AI Scans" (quick access)
2. **Create Custom Scan** → Set parameters
3. **Run Scan** → Get results
4. **Switch to Options** → Analyze strategies
5. **Use Copilot** → Advanced analysis

### **Options Trading Flow**
1. **Home** → "AI Options"
2. **Set Parameters** → Symbol, risk, portfolio
3. **Get Recommendations** → Review strategies
4. **Tap "Copilot"** → Deep analysis
5. **Analyze Greeks** → Make trading decision

---

## ✅ **Navigation Verification**

**All paths tested and working**:
- [x] Home → AI Tools → AI Scans
- [x] Home → AI Tools → AI Options  
- [x] Bottom Tab → AI Scans
- [x] AI Options → Options Copilot
- [x] AI Scans → Scan Details
- [x] Back navigation from all screens
- [x] Modal dialogs and overlays
- [x] Tab switching within screens

**Ready for production use!** 🎉
