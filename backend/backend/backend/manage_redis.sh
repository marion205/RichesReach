#!/bin/bash
# Redis Management Script for RichesReach

case "$1" in
    start)
        echo "Starting Redis..."
        redis-server redis_production.conf
        ;;
    stop)
        echo "Stopping Redis..."
        redis-cli shutdown
        ;;
    restart)
        echo "Restarting Redis..."
        redis-cli shutdown
        sleep 2
        redis-server redis_production.conf
        ;;
    status)
        echo "Redis status:"
        redis-cli ping
        ;;
    monitor)
        echo "Monitoring Redis..."
        redis-cli monitor
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|monitor}"
        exit 1
        ;;
esac
