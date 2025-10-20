# 🚀 **UI Testing Guide - Local Development**

## **Quick Start**

### **Option 1: Use the Start Script**
```bash
./start_local_dev.sh
```
Choose option 3 to start both servers in separate terminals.

### **Option 2: Manual Start**

#### **Start Django Backend:**
```bash
cd backend/backend
source ../venv/bin/activate
python3 manage.py runserver 127.0.0.1:8000 --settings=richesreach.settings_local
```

#### **Start React Native Frontend:**
```bash
cd mobile
npx expo start --clear --port 8081
```

## **🧪 Testing the Advanced Features**

### **1. 📧 Email Notifications**
- **KYC Workflow**: Start a KYC process and watch for email notifications
- **Trading Notifications**: Place orders and receive confirmation emails
- **Status Updates**: Get notified when orders are filled

### **2. 🔔 WebSocket Real-time Updates**
- **Order Updates**: Watch orders update in real-time
- **KYC Progress**: See KYC steps complete live
- **Market Data**: Real-time price updates for watched stocks

### **3. 📊 Analytics & Reporting**
- **Portfolio Analytics**: View comprehensive performance metrics
- **Risk Assessment**: See volatility and concentration analysis
- **Trading Performance**: Win rate, Sharpe ratio, and more

### **4. 🔐 KYC Workflow**
- **Step-by-step Process**: Complete the 7-step KYC workflow
- **Document Upload**: Test document verification
- **State Eligibility**: Check crypto trading eligibility

### **5. 📈 Trading Features**
- **Real Alpaca Integration**: Place actual orders (sandbox mode)
- **Stock Trading**: Buy/sell stocks and ETFs
- **Crypto Trading**: Trade cryptocurrencies (28 US states supported)

## **🎯 Key UI Screens to Test**

### **Trading Screen** (`/trading`)
- Real Alpaca account integration
- Order placement with live validation
- Position tracking and P&L
- Account status and buying power

### **KYC Workflow** (`/kyc`)
- 7-step guided process
- Document upload and verification
- Real-time progress tracking
- Email notifications at each step

### **Crypto Trading** (`/crypto`)
- State eligibility checking
- Popular crypto pairs (BTC/USD, ETH/USD)
- Real-time balance updates
- On-chain transfer capabilities

### **Analytics Dashboard** (`/analytics`)
- Portfolio performance metrics
- Risk analysis and recommendations
- Trading activity insights
- Automated report generation

## **🔍 Testing Checklist**

### **Backend Features**
- [ ] Django server running on http://localhost:8000
- [ ] GraphQL endpoint accessible at http://localhost:8000/graphql/
- [ ] Alpaca API integration working
- [ ] Email notifications sending
- [ ] WebSocket connections established

### **Frontend Features**
- [ ] React Native app running on Expo
- [ ] Trading screen with real data
- [ ] KYC workflow functional
- [ ] Crypto trading enabled
- [ ] Analytics dashboard populated

### **Integration Features**
- [ ] Real-time order updates
- [ ] Email notifications working
- [ ] WebSocket data streaming
- [ ] Analytics calculations accurate
- [ ] Error handling graceful

## **🚨 Troubleshooting**

### **Django Server Issues**
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing Django processes
pkill -f "manage.py runserver"

# Restart with verbose output
python3 manage.py runserver --verbosity=2
```

### **React Native Issues**
```bash
# Clear Metro cache
npx expo start --clear

# Reset React Native cache
npx react-native start --reset-cache

# Check if port 8081 is in use
lsof -i :8081
```

### **Database Issues**
```bash
# Run migrations
python3 manage.py migrate --settings=richesreach.settings_local

# Create superuser
python3 manage.py createsuperuser --settings=richesreach.settings_local
```

## **📱 Mobile App Testing**

### **iOS Simulator**
```bash
# Start iOS simulator
npx expo start --ios
```

### **Android Emulator**
```bash
# Start Android emulator
npx expo start --android
```

### **Physical Device**
```bash
# Scan QR code with Expo Go app
npx expo start
```

## **🎉 Success Indicators**

When everything is working correctly, you should see:

1. **Django Backend**: `Starting development server at http://127.0.0.1:8000/`
2. **Metro Bundler**: `Metro waiting on exp://192.168.x.x:8081`
3. **GraphQL**: Schema introspection working
4. **Alpaca**: API connections established
5. **Email**: Notifications sending successfully
6. **WebSocket**: Real-time updates flowing
7. **Analytics**: Performance metrics calculating

## **🚀 Ready to Test!**

Your RichesReach app now has enterprise-grade features:
- ✅ Real money trading with Alpaca
- ✅ Complete KYC/AML workflow
- ✅ Email notifications
- ✅ WebSocket real-time updates
- ✅ Advanced analytics
- ✅ End-to-end testing

**Happy testing!** 🎉
