# How to Access New Features 🚀

## 📱 Mobile App Features

### 1. Family Sharing Features

#### **SharedOrb** (Real-time Family Orb)
**Access Path:**
1. Open the app
2. Navigate to the **Portfolio** tab (bottom navigation)
3. If you have a family group, the **SharedOrb** will automatically appear instead of the regular Constellation Orb
4. You'll see real-time sync with other family members

**What you'll see:**
- Real-time orb that syncs with family members
- Family members indicator at the top showing who's viewing
- Recent activity feed showing family interactions
- Connection status: "Real-time" (WebSocket) or "Syncing" (HTTP fallback)

#### **Family Management** (Create/Manage Family Groups)
**Access Path:**
1. Open the app
2. Navigate to the **Portfolio** tab
3. Look for the **👥 (users)** button in the top-right corner of the header
4. Tap it to open the Family Management modal

**What you can do:**
- **Create Family Group**: Tap "Create Family Group" and enter a name
- **Invite Members**: Enter email addresses and select roles (Member/Teen)
- **Manage Permissions**: Control what each member can see/do
- **View Members**: See all family members in your group
- **Parental Controls**: Set restrictions for teen accounts

**Visual Indicator:**
- **👥 with badge**: Shows member count when you have a family group
- **👤+**: Shows when you don't have a family group yet

---

### 2. Privacy Dashboard

**Access Path:**
1. Open the app
2. Navigate to the **Profile** tab (bottom navigation)
3. Tap the **⋮ (three dots)** menu button in the top-right corner
4. Select **"Privacy & Data"** from the dropdown menu

**What you can do:**
- **View Data Usage**: See exactly what data is being used by AI/ML
- **Toggle Privacy Settings**:
  - Financial Data sharing
  - AI Analysis
  - ML Predictions
  - Analytics
  - Session Tracking
- **View Data Categories**: See retention periods and purposes
- **Data Orb Visualization**: Visual representation of your data usage

**Features:**
- Transparent AI explanations
- Opt-in/opt-out controls
- Data retention information
- Real-time privacy settings

---

### 3. Constellation Orb Gestures (Enhanced)

**Access Path:**
1. Navigate to **Portfolio** tab
2. The Constellation Orb (or SharedOrb) is displayed

**Available Gestures:**
- **Tap**: Life Events & Goals
- **Double Tap**: Quick Actions (Add Funds, Transfer, Analyze, etc.)
- **Long Press**: Detailed Breakdown (AI Recommendations included)
- **Swipe Left**: Market Crash Shield
- **Swipe Right**: Growth Projections (ML-enhanced)
- **Pinch**: What-If Simulator

**New AI/ML Features:**
- **AI Life Event Suggestions**: Personalized goals based on your profile
- **ML Growth Projections**: ML-predicted growth rates (not static)
- **AI Shield Analysis**: Real-time market analysis for protection
- **Personalized Recommendations**: AI-generated suggestions in Detailed Breakdown

---

## 🌐 Web App Features

### 4. Web Constellation Orb

**Access Path:**
1. Open your web browser
2. Navigate to: `http://localhost:5173` (development) or your production URL
3. The **OrbRenderer** will display automatically

**Features:**
- 3D orb visualization using Three.js
- Interactive gestures (mouse/touch)
- Real-time net worth display
- PWA support (installable for offline access)

**To Install as PWA:**
1. Visit the web app
2. Look for the "Install App" button in the footer
3. Click to install for offline access

---

## 🎯 Quick Reference

### Family Sharing
```
Portfolio Tab → 👥 Button → Family Management
```

### Privacy Settings
```
Profile Tab → ⋮ Menu → Privacy & Data
```

### Web Orb
```
Browser → http://localhost:5173
```

### Orb Gestures
```
Portfolio Tab → Constellation Orb → Various Gestures
```

---

## 🔍 Visual Indicators

### Family Sharing Status
- **🟢 Real-time**: WebSocket connected, instant updates
- **🟡 Syncing...**: HTTP fallback active
- **⚪ Synced**: Initial state loaded

### AI/ML Features
- **"AI" badge**: Shows when AI features are active
- **"ML" badge**: Shows when ML predictions are active
- **Loading indicators**: Shows when AI/ML is processing

### Family Group
- **👥 with number badge**: Family group exists (shows member count)
- **👤+**: No family group (tap to create)

---

## 📝 Step-by-Step Guides

### Creating Your First Family Group

1. **Open Portfolio Tab**
   - Tap the Portfolio icon in bottom navigation

2. **Tap Family Button**
   - Look for 👥 or 👤+ in top-right corner
   - Tap it

3. **Create Group**
   - Tap "Create Family Group"
   - Enter a name (e.g., "The Smith Family")
   - Tap "Create"

4. **Invite Members**
   - Enter email address
   - Select role (Member or Teen)
   - Tap "Send Invite"

5. **Start Sharing**
   - SharedOrb appears automatically
   - Family members can now see real-time updates

### Accessing Privacy Dashboard

1. **Open Profile Tab**
   - Tap the Profile icon in bottom navigation

2. **Open Settings Menu**
   - Tap the ⋮ (three dots) in top-right corner

3. **Select Privacy**
   - Tap "Privacy & Data" from the menu

4. **Manage Settings**
   - Toggle data sharing options
   - View data usage
   - Adjust retention settings

### Using Web App

1. **Start Development Server** (if needed)
   ```bash
   cd web
   npm install
   npm run dev
   ```

2. **Open Browser**
   - Navigate to `http://localhost:5173`

3. **View Orb**
   - Orb displays automatically
   - Interact with mouse/touch gestures

4. **Install PWA** (optional)
   - Click "Install App" button
   - Follow browser prompts

---

## 🎉 All Features Summary

| Feature | Location | Access Method |
|---------|----------|---------------|
| **SharedOrb** | Portfolio Tab | Automatic (when family group exists) |
| **Family Management** | Portfolio Tab | Tap 👥 button |
| **Privacy Dashboard** | Profile Tab | Tap ⋮ → Privacy & Data |
| **AI Life Events** | Portfolio Tab | Tap orb → Life Events |
| **ML Growth Projections** | Portfolio Tab | Swipe right on orb |
| **AI Shield Analysis** | Portfolio Tab | Swipe left on orb |
| **AI Recommendations** | Portfolio Tab | Long press orb |
| **Web Orb** | Browser | Visit web app URL |

---

## 💡 Tips

1. **Family Sharing**: Create a family group first, then invite members. The SharedOrb appears automatically once you have a group.

2. **Privacy**: Check your privacy settings regularly. The dashboard shows exactly what data is being used.

3. **Web App**: The web app works best on desktop browsers. Mobile browsers also supported.

4. **Gestures**: Practice the different gestures on the orb to discover all features.

5. **Real-time Sync**: Look for the "Real-time" indicator to confirm WebSocket connection is active.

---

**Need Help?** All features are fully integrated and ready to use! 🚀

