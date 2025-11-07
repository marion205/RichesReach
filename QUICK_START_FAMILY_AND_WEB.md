# Quick Start: Family Sharing & Web/PWA

## 🎯 What's Ready

### ✅ Family Sharing (Mobile)
- Complete service layer
- SharedOrb component with real-time sync
- Family management UI
- Parental controls
- Backend API endpoints

### ✅ Web/PWA
- Three.js orb renderer
- PWA manifest and service worker
- Responsive web app
- SEO optimized

## 🚀 Integration Steps

### 1. Add Family Sharing to PortfolioScreen (5 minutes)

```typescript
// In PortfolioScreen.tsx, add:
import { SharedOrb } from '../../family/components/SharedOrb';
import { FamilyManagementModal } from '../../family/components/FamilyManagementModal';
import { familySharingService } from '../../family/services/FamilySharingService';

// Add state:
const [familyGroup, setFamilyGroup] = useState(null);
const [showFamilyModal, setShowFamilyModal] = useState(false);

// Load family group on mount:
useEffect(() => {
  familySharingService.getFamilyGroup().then(setFamilyGroup);
}, []);

// Replace ConstellationOrb with SharedOrb if in family:
{familyGroup ? (
  <SharedOrb
    snapshot={snapshot}
    familyGroupId={familyGroup.id}
    currentUser={familyGroup.members.find(m => m.userId === currentUserId)}
    onGesture={handleGesture}
  />
) : (
  <ConstellationOrb snapshot={snapshot} {...gestureHandlers} />
)}

// Add family button to header:
<TouchableOpacity onPress={() => setShowFamilyModal(true)}>
  <Icon name="users" size={24} color="#007AFF" />
</TouchableOpacity>

// Add modal:
<FamilyManagementModal
  visible={showFamilyModal}
  onClose={() => setShowFamilyModal(false)}
  onFamilyCreated={setFamilyGroup}
/>
```

### 2. Set Up Web App (10 minutes)

```bash
cd web
npm install
npm run dev
```

Visit `http://localhost:5173` to see the orb!

### 3. Deploy Web to Production

```bash
npm run build
# Deploy dist/ folder to Vercel/Netlify
```

## 📱 Testing Family Sharing

1. **Create Family Group**
   - Open app → Settings → Family
   - Tap "Create Family Group"
   - Should see your family group

2. **Invite Member**
   - Enter email address
   - Select role (Member or Teen)
   - Tap "Send Invite"
   - Share invite code

3. **Accept Invite** (on another device/account)
   - Enter invite code
   - Should join family group

4. **Test Shared Orb**
   - Both users should see each other
   - Gestures should sync
   - Activity feed should show interactions

## 🌐 Testing Web/PWA

1. **Local Development**
   ```bash
   cd web
   npm install
   npm run dev
   ```

2. **Install PWA**
   - Open in Chrome/Edge
   - Click install prompt
   - Should install as app

3. **Test Offline**
   - Install PWA
   - Turn off internet
   - App should still work (cached)

4. **Test Gestures**
   - Click orb → tap gesture
   - Swipe → swipe gesture
   - Scroll wheel → pinch gesture

## 🎯 Next Priorities

1. **Backend Database** (Week 1)
   - Create FamilyGroup model
   - Create FamilyMember model
   - Add migrations

2. **WebSocket Real-time** (Week 2)
   - Set up WebSocket server
   - Real-time orb sync
   - Gesture broadcasting

3. **Web Deployment** (Week 2)
   - Deploy to Vercel/Netlify
   - Configure domain
   - Set up analytics

## 📊 Success Metrics

Track these in Amplitude/Mixpanel:

- **Family Sharing:**
  - % users in family groups
  - Average family size
  - Daily active family members
  - Invite acceptance rate

- **Web/PWA:**
  - Web traffic growth
  - PWA install rate
  - SEO ranking
  - Conversion rate (web → mobile)

---

**You're ready to launch!** 🚀

The foundation is complete. Next step: integrate into PortfolioScreen and deploy web app.

