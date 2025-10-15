#!/bin/bash

# ECS Instance User Data Script

# Update system
yum update -y

# Install CloudWatch agent
yum install -y amazon-cloudwatch-agent

# Configure CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
    "metrics": {
        "namespace": "ECS/EC2",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60
            },
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "diskio": {
                "measurement": [
                    "io_time"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    }
}
EOF

# Start CloudWatch agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
    -s

# Configure ECS agent
echo ECS_CLUSTER=${cluster_name} >> /etc/ecs/ecs.config
echo ECS_ENABLE_TASK_IAM_ROLE=true >> /etc/ecs/ecs.config
echo ECS_ENABLE_TASK_CPU_MEM_LIMIT=true >> /etc/ecs/ecs.config

# Start ECS agent
start ecs

# Install additional monitoring tools
yum install -y htop iotop

# Configure log rotation for ECS
cat > /etc/logrotate.d/ecs << EOF
/var/log/ecs/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 644 root root
    postrotate
        /bin/kill -HUP \`cat /var/run/rsyslogd.pid 2> /dev/null\` 2> /dev/null || true
    endscript
}
EOF

# Set up log aggregation
mkdir -p /var/log/riches-reach
chown ec2-user:ec2-user /var/log/riches-reach

# Configure system limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf
echo "* soft nproc 65536" >> /etc/security/limits.conf
echo "* hard nproc 65536" >> /etc/security/limits.conf

# Optimize kernel parameters
cat >> /etc/sysctl.conf << EOF
# Network optimizations
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_timestamps = 1
net.ipv4.tcp_sack = 1

# File system optimizations
fs.file-max = 2097152
vm.max_map_count = 262144
EOF

# Apply sysctl changes
sysctl -p

# Create monitoring script
cat > /usr/local/bin/ecs-monitor.sh << 'EOF'
#!/bin/bash

# ECS Monitoring Script
LOG_FILE="/var/log/riches-reach/ecs-monitor.log"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}

# Check ECS agent status
if ! systemctl is-active --quiet ecs; then
    log_message "ERROR: ECS agent is not running"
    systemctl restart ecs
    log_message "INFO: ECS agent restarted"
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    log_message "WARNING: Disk usage is ${DISK_USAGE}%"
fi

# Check memory usage
MEM_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ $MEM_USAGE -gt 90 ]; then
    log_message "WARNING: Memory usage is ${MEM_USAGE}%"
fi

# Check running tasks
TASK_COUNT=$(docker ps --format "table {{.Names}}" | grep -c "ecs-")
log_message "INFO: Running tasks: $TASK_COUNT"
EOF

chmod +x /usr/local/bin/ecs-monitor.sh

# Add monitoring to crontab
echo "*/5 * * * * /usr/local/bin/ecs-monitor.sh" | crontab -

log_message "INFO: ECS instance initialization completed"
