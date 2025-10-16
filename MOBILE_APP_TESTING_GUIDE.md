# 📱 RichesReach Mobile App Testing Guide

## 🎯 **Testing Mobile App with Production API**

Your mobile app is now configured to connect to your production servers at `http://54.160.139.56:8000`. Here's how to test it locally before releasing to app stores.

## ✅ **What's Already Set Up**

### **1. Production API Connection**
- ✅ **API Base URL**: `http://54.160.139.56:8000`
- ✅ **GraphQL Endpoint**: `http://54.160.139.56:8000/graphql/`
- ✅ **Health Check**: `http://54.160.139.56:8000/healthz`
- ✅ **Authentication**: `http://54.160.139.56:8000/me/`

### **2. Configuration Files Updated**
- ✅ `mobile/src/config/api.ts` - Updated with production server IP
- ✅ `mobile/env.local.production` - Local development environment file
- ✅ `mobile/test-production-connection.js` - Connection test script

### **3. Production API Verified**
- ✅ Health endpoint working
- ✅ GraphQL endpoint responding correctly
- ✅ Authentication endpoint accessible
- ✅ All security measures in place

## 🚀 **How to Run the Mobile App**

### **Step 1: Install Expo Go on Your Phone**
1. **iOS**: Download "Expo Go" from the App Store
2. **Android**: Download "Expo Go" from Google Play Store

### **Step 2: Start the Development Server**
```bash
# Navigate to mobile directory
cd mobile

# Make sure you're using Node 22
nvm use 22

# Install dependencies (if needed)
npm install

# Start the Expo development server
npx expo start
```

### **Step 3: Connect Your Phone**
1. **Scan QR Code**: Use your phone's camera or Expo Go app to scan the QR code
2. **Same Network**: Make sure your phone and computer are on the same WiFi network
3. **Alternative**: Use tunnel mode if on different networks:
   ```bash
   npx expo start --tunnel
   ```

### **Step 4: Test the App**
Once connected, you can test:
- ✅ **Authentication Flow** - Login/register functionality
- ✅ **GraphQL Queries** - Stock data, portfolio, etc.
- ✅ **Real-time Data** - Live market data from production
- ✅ **All Features** - Complete app functionality

## 🧪 **Testing Checklist**

### **Core Functionality**
- [ ] **App Launches** - No crashes on startup
- [ ] **API Connection** - Successfully connects to production
- [ ] **Authentication** - Login/register works
- [ ] **GraphQL Queries** - Data loads correctly
- [ ] **Navigation** - All screens accessible
- [ ] **Performance** - Smooth scrolling and interactions

### **Production API Features**
- [ ] **Stock Data** - Real market data loading
- [ ] **Portfolio** - User portfolio functionality
- [ ] **Authentication** - JWT token handling
- [ ] **Real-time Updates** - Live data feeds
- [ ] **Error Handling** - Graceful error messages
- [ ] **Offline Handling** - Network error recovery

### **Security Features**
- [ ] **HTTPS Requests** - Secure API calls
- [ ] **Token Storage** - Secure JWT storage
- [ ] **Data Validation** - Input validation working
- [ ] **Error Messages** - No sensitive data exposed

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. "Network Error" or "Connection Failed"**
```bash
# Check if production server is running
curl http://54.160.139.56:8000/healthz

# Should return: {"ok": true, "app": "richesreach"}
```

#### **2. "Expo Go Can't Connect"**
- Make sure both devices are on the same WiFi
- Try tunnel mode: `npx expo start --tunnel`
- Check firewall settings

#### **3. "GraphQL Errors"**
- Verify the GraphQL endpoint: `http://54.160.139.56:8000/graphql/`
- Check network tab in Expo Go for detailed errors

#### **4. "Authentication Issues"**
- Test auth endpoint: `curl http://54.160.139.56:8000/me/`
- Check JWT token handling in the app

### **Debug Commands**
```bash
# Test production API connection
node test-production-connection.js

# Check Expo server status
npx expo doctor

# Clear Expo cache
npx expo start --clear

# Run in development mode with logs
npx expo start --dev-client
```

## 📊 **Expected Results**

### **Successful Connection**
When everything works correctly, you should see:
- ✅ App loads without errors
- ✅ API calls succeed (check network tab)
- ✅ Real data loads from production
- ✅ Authentication works
- ✅ All features functional

### **Performance Expectations**
- **App Launch**: <3 seconds
- **API Response**: <2 seconds (production server)
- **Navigation**: Smooth transitions
- **Data Loading**: Real-time updates

## 🎯 **Pre-Release Testing**

### **Critical Tests Before App Store Release**

#### **1. Authentication Flow**
- [ ] User registration works
- [ ] Login with valid credentials
- [ ] Logout functionality
- [ ] Password reset (if implemented)
- [ ] JWT token refresh

#### **2. Core Features**
- [ ] Stock data loading
- [ ] Portfolio management
- [ ] Real-time price updates
- [ ] Chart rendering
- [ ] Search functionality

#### **3. Error Handling**
- [ ] Network connectivity issues
- [ ] API server errors
- [ ] Invalid user input
- [ ] Authentication failures

#### **4. Performance**
- [ ] App startup time
- [ ] Data loading speed
- [ ] Memory usage
- [ ] Battery consumption

## 🚀 **Ready for App Store Release**

Once all tests pass:

### **iOS App Store**
1. **Build for iOS**: `npx expo build:ios`
2. **Test on TestFlight**: Upload to TestFlight for beta testing
3. **Submit for Review**: Submit to App Store Connect

### **Google Play Store**
1. **Build for Android**: `npx expo build:android`
2. **Test on Internal Testing**: Upload to Google Play Console
3. **Submit for Review**: Submit to Google Play Store

## 📱 **Production API Benefits**

Testing with your production API provides:
- ✅ **Real Data** - Actual market data and user accounts
- ✅ **Performance Testing** - Real server response times
- ✅ **Security Validation** - Production security measures
- ✅ **End-to-End Testing** - Complete user experience
- ✅ **Pre-Release Confidence** - Know it works before launch

## 🎉 **Success Criteria**

Your app is ready for app store release when:
- ✅ All core features work with production API
- ✅ Authentication flow is smooth
- ✅ Performance meets expectations
- ✅ Error handling is graceful
- ✅ Security measures are working
- ✅ User experience is polished

---

**📱 Your RichesReach mobile app is now ready for comprehensive testing with the production API!**

The setup provides a complete end-to-end testing environment that mirrors exactly what users will experience when the app is released to the app stores.
