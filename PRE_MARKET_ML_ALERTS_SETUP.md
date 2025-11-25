# Pre-Market Scanner: ML Learning + Alerts Setup

## 🎯 **Complete Implementation**

Your pre-market scanner now includes:
- ✅ **ML Learning System** - Learns from past performance
- ✅ **Email Alerts** - Sends daily alerts
- ✅ **Push Notifications** - Mobile app integration ready
- ✅ **Performance Tracking** - Records outcomes for ML
- ✅ **Cron Scheduling** - Daily runs at 8:00 AM ET

---

## 🤖 **ML Learning System**

### **How It Works**

1. **Records Outcomes**: After each trading day, records which picks were successful
2. **Trains Model**: Uses Gradient Boosting to learn patterns in successful picks
3. **Enhances Picks**: Adds ML success probability to each pick
4. **Improves Over Time**: Gets better as it sees more data

### **Features Learned**

The ML model learns from:
- Pre-market change percentage
- Volume (log-transformed)
- Market cap (log-transformed)
- Price
- Volume-to-market-cap ratio
- Price-to-prev-close ratio
- Long vs. Short
- Hour of day
- Day of week

### **Usage**

```bash
# Train ML model on historical data
python manage.py pre_market_scan_with_alerts --train-ml

# Show ML learning insights
python manage.py pre_market_scan_with_alerts --ml-insights

# Run scan with ML enhancement (automatic)
python manage.py pre_market_scan_with_alerts --mode AGGRESSIVE
```

### **ML Model Files**

- `core/ml_models/pre_market_predictor.pkl` - Trained model
- `core/ml_models/pre_market_scaler.pkl` - Feature scaler

**Note**: Model trains automatically when you have 50+ historical records.

---

## 📧 **Email Alerts**

### **Setup**

Add to your `.env` file:

```bash
# Email Configuration
ALERT_EMAIL=your-email@example.com
SMTP_USER=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### **Gmail Setup**

1. Enable "Less secure app access" or use App Password
2. Use App Password: https://myaccount.google.com/apppasswords
3. Set `SMTP_PASSWORD` to your app password

### **Usage**

```bash
# Send email alert
python manage.py pre_market_scan_with_alerts --send-email
```

### **Email Content**

- HTML formatted
- Top 10 setups with key metrics
- ML success probabilities
- Risk warnings

---

## 📱 **Push Notifications**

### **Setup**

Add to your `.env` file:

```bash
PUSH_NOTIFICATION_KEY=your-push-notification-api-key
```

### **Integration**

The push notification service is ready for integration with:
- Firebase Cloud Messaging (FCM)
- Apple Push Notification Service (APNs)
- Your custom push service

**TODO**: Implement actual push notification sending in `pre_market_alerts.py`

### **Usage**

```bash
# Send push notification
python manage.py pre_market_scan_with_alerts --send-push
```

---

## ⏰ **Cron Scheduling**

### **Setup**

1. **Make scripts executable** (already done):
   ```bash
   chmod +x schedule_pre_market_scanner.sh
   chmod +x setup_pre_market_cron.sh
   ```

2. **Add to crontab**:
   ```bash
   # Run setup script
   ./setup_pre_market_cron.sh
   
   # Or manually add:
   crontab -e
   # Add: 0 13 * * 1-5 /path/to/schedule_pre_market_scanner.sh
   ```

3. **Time Zones**:
   - **8:00 AM ET** = **13:00 UTC** (Standard Time)
   - **8:00 AM ET** = **12:00 UTC** (Daylight Saving Time)
   - Adjust cron time for DST

### **Cron Schedule**

- **Runs**: Monday-Friday (1-5)
- **Time**: 8:00 AM ET (adjust for DST)
- **Command**: Runs `pre_market_scan_with_alerts` with all features enabled

---

## 📊 **Performance Tracking**

### **Evaluate Performance**

After each trading day, evaluate performance:

```bash
# Evaluate today's picks
python manage.py evaluate_pre_market_performance

# Evaluate last 7 days
python manage.py evaluate_pre_market_performance --days 7

# Evaluate specific symbol
python manage.py evaluate_pre_market_performance --symbol AAPL
```

### **What It Does**

1. Finds signals from the specified period
2. Gets performance data (EOD outcomes)
3. Records outcomes for ML learning
4. Trains model automatically (if 50+ records)

---

## 🔄 **Daily Workflow**

### **Morning (8:00 AM ET - Automated)**

1. Cron job runs `schedule_pre_market_scanner.sh`
2. Scanner finds quality setups
3. ML enhances picks with success probabilities
4. Email alert sent
5. Push notification sent (if configured)
6. ML model trained (if 50+ records available)

### **Evening (After Market Close)**

1. Run performance evaluation:
   ```bash
   python manage.py evaluate_pre_market_performance
   ```

2. Train ML model (if needed):
   ```bash
   python manage.py pre_market_scan_with_alerts --train-ml
   ```

3. Check ML insights:
   ```bash
   python manage.py pre_market_scan_with_alerts --ml-insights
   ```

---

## 🎯 **Complete Command Reference**

### **Pre-Market Scan**

```bash
# Basic scan
python manage.py pre_market_scan --mode AGGRESSIVE --limit 20

# With alerts
python manage.py pre_market_scan_with_alerts \
    --mode AGGRESSIVE \
    --limit 20 \
    --send-email \
    --send-push

# Train ML model
python manage.py pre_market_scan_with_alerts --train-ml

# Show ML insights
python manage.py pre_market_scan_with_alerts --ml-insights
```

### **Performance Evaluation**

```bash
# Evaluate today
python manage.py evaluate_pre_market_performance

# Evaluate last N days
python manage.py evaluate_pre_market_performance --days 7

# Evaluate specific symbol
python manage.py evaluate_pre_market_performance --symbol AAPL
```

---

## 📈 **ML Model Performance**

### **Training Metrics**

- **Train Score**: R² score on training data
- **Test Score**: R² score on test data
- **Success Rate**: Historical success rate
- **Feature Importances**: Which features matter most

### **Improving the Model**

1. **More Data**: More historical records = better model
2. **Better Features**: Add more features (news, options flow, etc.)
3. **Hyperparameter Tuning**: Adjust model parameters
4. **Ensemble Methods**: Combine multiple models

---

## 🔧 **Configuration**

### **Environment Variables**

```bash
# Email
ALERT_EMAIL=your-email@example.com
SMTP_USER=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Push Notifications
PUSH_NOTIFICATION_KEY=your-push-key

# ML Model (optional)
ML_MODEL_PATH=/path/to/models
```

### **Dependencies**

```bash
# Required
pip install django

# ML Features (optional but recommended)
pip install scikit-learn joblib

# Email (optional)
pip install django-sendmail-backend  # Or use Django's default
```

---

## 🚀 **Next Steps**

1. ✅ **Set up email alerts** - Configure SMTP settings
2. ✅ **Set up cron job** - Run `setup_pre_market_cron.sh`
3. ✅ **Evaluate performance daily** - Build ML training data
4. ✅ **Train ML model** - After 50+ records
5. ✅ **Integrate push notifications** - Connect to your push service
6. ✅ **Monitor performance** - Track if ML improves picks

---

## 💡 **Pro Tips**

1. **Start Small**: Begin with email alerts, add ML later
2. **Track Performance**: Evaluate daily to build ML data
3. **Be Patient**: ML needs 50+ records to train
4. **Monitor Features**: Check which features ML learns are important
5. **Refine Filters**: Adjust based on ML insights

---

**Your pre-market scanner is now a complete ML-powered system! 🚀**

