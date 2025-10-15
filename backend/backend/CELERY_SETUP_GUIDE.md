# Celery Setup Guide for RichesReach

## 🚀 **Celery Configuration Complete!**

### ✅ **What's Been Set Up**

1. **Celery Configuration** (`celery_config.py`)
   - Production-ready Celery app configuration
   - Redis broker and result backend
   - Task routing and queues
   - Periodic task scheduling
   - Error handling and monitoring

2. **Redis Setup** (`setup_redis.py`)
   - Redis installation and configuration
   - Connection testing
   - Production configuration template
   - Management scripts

3. **Worker Management** (`start_celery_worker.py`)
   - Worker startup scripts
   - Beat scheduler management
   - Flower monitoring setup
   - Health checks

### 🔧 **Celery Components**

#### **1. Celery Worker**
- Processes background tasks
- Handles swing trading signal generation
- Updates OHLCV indicators
- Validates signals and updates trader scores

#### **2. Celery Beat Scheduler**
- Runs periodic tasks
- Scans symbols for signals every 5 minutes
- Updates indicators every hour
- Validates signals every 30 minutes
- Updates trader scores daily
- Cleans up old data weekly

#### **3. Celery Flower (Monitoring)**
- Web-based monitoring interface
- Task execution monitoring
- Worker status tracking
- Performance metrics

### 📋 **Periodic Tasks Configured**

| Task | Frequency | Description |
|------|-----------|-------------|
| `scan_symbol_for_signals` | Every 5 minutes | Scans symbols for new trading signals |
| `update_ohlcv_indicators` | Every hour | Updates technical indicators |
| `validate_signals` | Every 30 minutes | Validates existing signals |
| `update_trader_scores` | Daily | Updates trader performance scores |
| `cleanup_old_data` | Weekly | Cleans up old data |
| `generate_daily_report` | Daily | Generates daily trading reports |
| `train_ml_models` | Daily | Retrains ML models |

### 🚀 **Starting Celery Components**

#### **Development Mode**
```bash
# Terminal 1: Start Celery Worker
python start_celery_worker.py worker

# Terminal 2: Start Celery Beat Scheduler
python start_celery_worker.py beat

# Terminal 3: Start Flower Monitoring (optional)
python start_celery_worker.py flower
```

#### **Production Mode**
```bash
# Start Redis (if not already running)
./manage_redis.sh start

# Start Celery Worker
celery -A celery_config worker --loglevel=info --concurrency=4

# Start Celery Beat Scheduler
celery -A celery_config beat --loglevel=info

# Start Flower Monitoring
celery -A celery_config flower --port=5555
```

### 🔍 **Monitoring and Health Checks**

#### **Check Redis Status**
```bash
redis-cli ping
# Should return: PONG
```

#### **Check Celery Worker Status**
```bash
celery -A celery_config inspect active
celery -A celery_config inspect stats
```

#### **Check Beat Scheduler Status**
```bash
celery -A celery_config inspect scheduled
```

#### **Access Flower Monitoring**
- URL: http://localhost:5555
- View task execution, worker status, and performance metrics

### 🛠 **Configuration Files**

#### **1. `celery_config.py`**
- Main Celery application configuration
- Task routing and queues
- Periodic task scheduling
- Error handling and monitoring

#### **2. `redis_production.conf`**
- Production Redis configuration
- Memory management settings
- Persistence configuration
- Security settings

#### **3. `manage_redis.sh`**
- Redis management script
- Start/stop/restart Redis
- Status monitoring

### 📊 **Task Queues**

| Queue | Purpose | Tasks |
|-------|---------|-------|
| `swing_trading` | Swing trading specific tasks | Signal generation, indicator updates |
| `general` | General application tasks | User notifications, cleanup |

### 🔒 **Security Considerations**

1. **Redis Security**
   - Set password in production
   - Bind to localhost only
   - Use SSL/TLS in production

2. **Celery Security**
   - Use secure broker URLs
   - Enable task result encryption
   - Monitor task execution

3. **Network Security**
   - Firewall configuration
   - VPN access for remote workers
   - SSL/TLS for all connections

### 🚨 **Troubleshooting**

#### **Common Issues**

1. **Redis Connection Failed**
   ```bash
   # Check if Redis is running
   redis-cli ping
   
   # Start Redis if not running
   redis-server
   ```

2. **Celery Worker Not Starting**
   ```bash
   # Check Django settings
   python manage.py check
   
   # Check Celery configuration
   python -c "from celery_config import app; print(app.conf.broker_url)"
   ```

3. **Tasks Not Executing**
   ```bash
   # Check worker status
   celery -A celery_config inspect active
   
   # Check beat scheduler
   celery -A celery_config inspect scheduled
   ```

#### **Log Files**
- Worker logs: Console output
- Beat logs: Console output
- Redis logs: `/var/log/redis/redis-server.log`

### 📈 **Performance Optimization**

#### **Worker Configuration**
- Adjust `--concurrency` based on CPU cores
- Use `--prefetch-multiplier=1` for CPU-bound tasks
- Set appropriate `--max-tasks-per-child`

#### **Redis Optimization**
- Configure memory limits
- Use appropriate persistence settings
- Monitor memory usage

#### **Task Optimization**
- Use appropriate task timeouts
- Implement task retry logic
- Monitor task execution times

### 🔄 **Deployment Checklist**

- [ ] Redis server running and accessible
- [ ] Celery worker started with appropriate concurrency
- [ ] Celery beat scheduler running
- [ ] Flower monitoring accessible (optional)
- [ ] Task queues configured correctly
- [ ] Periodic tasks scheduled
- [ ] Error handling configured
- [ ] Monitoring and alerting set up
- [ ] Log rotation configured
- [ ] Backup procedures in place

### 🎯 **Next Steps**

1. **Start Celery Components**
   ```bash
   python start_celery_worker.py all
   ```

2. **Test Task Execution**
   ```bash
   python -c "from celery_config import debug_task; debug_task.delay()"
   ```

3. **Monitor Performance**
   - Access Flower at http://localhost:5555
   - Check Redis memory usage
   - Monitor task execution times

4. **Configure Production**
   - Update Redis configuration
   - Set up process management (systemd, supervisor)
   - Configure monitoring and alerting

## 🎉 **Celery Setup Complete!**

Your Celery configuration is now ready for production use with:
- ✅ Redis broker and result backend
- ✅ Task routing and queues
- ✅ Periodic task scheduling
- ✅ Error handling and monitoring
- ✅ Production-ready configuration
- ✅ Management scripts and tools

The swing trading platform now has a robust background task processing system that can handle:
- Real-time signal generation
- Technical indicator updates
- Data validation and cleanup
- ML model training
- Performance monitoring
- Automated reporting
