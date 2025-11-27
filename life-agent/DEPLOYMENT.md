# 🚀 Deployment Guide

Complete guide for deploying Life Agent to production.

## Local Development Setup

### Requirements
- Python 3.11+
- PostgreSQL 15+
- Playwright
- Git

### Steps

```bash
# Clone repository
git clone <your-repo>
cd life-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Setup database
createdb lifeagent
cp .env.example .env
# Edit .env with your credentials

# Run migrations
alembic upgrade head

# Start agent
python main.py
```

## Docker Deployment (Recommended)

### Local Docker

```bash
# Navigate to project
cd life-agent

# Configure
cp .env.example .env
# Edit .env with your API keys

# Build and run
docker-compose up -d

# View logs
docker-compose logs -f agent

# Stop
docker-compose down
```

### VPS Deployment (DigitalOcean, AWS, etc.)

#### 1. Provision Server

**Recommended specs:**
- CPU: 2 cores
- RAM: 2GB minimum (4GB recommended)
- Storage: 20GB
- OS: Ubuntu 22.04 LTS

#### 2. Initial Server Setup

```bash
# SSH into server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Create non-root user (optional but recommended)
adduser agent
usermod -aG docker agent
su - agent
```

#### 3. Deploy Application

```bash
# Clone repository
git clone <your-repo>
cd life-agent

# Configure
cp .env.example .env
nano .env  # Add your API keys

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f agent
```

#### 4. Setup Auto-restart

Create systemd service:

```bash
sudo nano /etc/systemd/system/life-agent.service
```

Add:
```ini
[Unit]
Description=Life Agent
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/agent/life-agent
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=agent

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable life-agent
sudo systemctl start life-agent
```

#### 5. Setup Firewall

```bash
# Install UFW
sudo apt install ufw

# Allow SSH
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

#### 6. Setup Monitoring

Install monitoring tools:

```bash
# Install htop for resource monitoring
sudo apt install htop

# Check Docker stats
docker stats

# Setup log rotation
sudo nano /etc/docker/daemon.json
```

Add:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Restart Docker:
```bash
sudo systemctl restart docker
docker-compose restart
```

## Cloud Platform Specific Guides

### DigitalOcean

1. Create Droplet
   - Choose Ubuntu 22.04
   - Select $6/month plan (2GB RAM)
   - Add SSH key
   - Create

2. Follow VPS deployment steps above

3. Optional: Setup floating IP for stability

### AWS Lightsail

1. Create instance
   - Choose OS Only → Ubuntu 22.04
   - Select $5/month plan
   - Create

2. Download SSH key

3. Connect and follow VPS deployment steps

### Hetzner

1. Create Cloud Server
   - Location: Choose closest to you
   - Image: Ubuntu 22.04
   - Type: CX11 (€4.5/month)
   - SSH key: Add your key
   - Create

2. Follow VPS deployment steps

## Database Backup Strategy

### Automated Backups

Create backup script:

```bash
nano ~/backup.sh
```

Add:
```bash
#!/bin/bash
BACKUP_DIR="/home/agent/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T db pg_dump -U agent lifeagent > $BACKUP_DIR/db_$DATE.sql

# Backup data files
tar -czf $BACKUP_DIR/data_$DATE.tar.gz data/

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Make executable:
```bash
chmod +x ~/backup.sh
```

Schedule with cron:
```bash
crontab -e
```

Add:
```
0 2 * * * /home/agent/backup.sh >> /home/agent/backup.log 2>&1
```

### Manual Backup

```bash
# Backup database
docker-compose exec db pg_dump -U agent lifeagent > backup.sql

# Backup files
tar -czf data-backup.tar.gz data/ logs/

# Download from server (on your local machine)
scp agent@your-server:/home/agent/life-agent/backup.sql .
scp agent@your-server:/home/agent/life-agent/data-backup.tar.gz .
```

### Restore Backup

```bash
# Restore database
cat backup.sql | docker-compose exec -T db psql -U agent lifeagent

# Restore files
tar -xzf data-backup.tar.gz
```

## Updating the Agent

### Docker Deployment

```bash
# Navigate to project
cd life-agent

# Pull latest changes (if using git)
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Check logs
docker-compose logs -f agent
```

### Rolling Back

```bash
# Stop current version
docker-compose down

# Checkout previous version
git checkout <previous-commit>

# Rebuild
docker-compose up -d --build
```

## Monitoring & Maintenance

### Health Checks

Create monitoring script:

```bash
nano ~/health-check.sh
```

Add:
```bash
#!/bin/bash

# Check if agent container is running
if ! docker-compose ps | grep -q "agent.*Up"; then
    echo "Agent is down! Restarting..."
    cd /home/agent/life-agent
    docker-compose restart agent
    
    # Send notification (optional - requires mail setup)
    # echo "Agent was restarted" | mail -s "Agent Health Check" your@email.com
fi
```

Schedule:
```bash
crontab -e
# Add: */5 * * * * /home/agent/health-check.sh
```

### Log Management

View logs:
```bash
# Real-time logs
docker-compose logs -f agent

# Last 100 lines
docker-compose logs --tail=100 agent

# Specific time range
docker-compose logs --since="2024-01-01T00:00:00" agent
```

### Resource Monitoring

```bash
# Container resource usage
docker stats

# Disk usage
df -h
du -sh /var/lib/docker

# Memory usage
free -h

# System monitoring
htop
```

## Scaling

### Horizontal Scaling

For high-traffic scenarios:

1. Use external PostgreSQL (AWS RDS, DigitalOcean Managed DB)
2. Deploy multiple agent instances
3. Use load balancer

### Vertical Scaling

Upgrade server resources:
- 4GB RAM for heavy usage
- 4 CPU cores for faster processing
- SSD storage for better performance

## Security Best Practices

### 1. API Key Security

```bash
# Never commit .env
echo ".env" >> .gitignore

# Use strong database password
# Rotate API keys regularly
```

### 2. Server Security

```bash
# Keep system updated
sudo apt update && sudo apt upgrade -y

# Setup automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades

# Disable root SSH login
sudo nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
sudo systemctl restart sshd
```

### 3. Docker Security

```bash
# Run containers as non-root user
# Limit container resources
# Keep Docker updated
```

## Troubleshooting

### Agent Not Starting

```bash
# Check logs
docker-compose logs agent

# Common issues:
# - Invalid API keys
# - Database connection failed
# - Port already in use
```

### Database Connection Issues

```bash
# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db

# Verify connection
docker-compose exec db psql -U agent lifeagent -c "SELECT 1"
```

### High Memory Usage

```bash
# Check container stats
docker stats

# Restart agent
docker-compose restart agent

# If persistent, increase server RAM
```

### Plugin Errors

```bash
# Check plugin logs
grep "plugin" logs/agent.log

# Disable problematic plugin
nano config/plugins.yaml
# Comment out plugin

# Restart
docker-compose restart agent
```

## Cost Optimization

### Minimize Costs

1. **Use spot instances** (AWS) for non-critical deployments
2. **Schedule downtime** if not needed 24/7
3. **Optimize database** - clean old data regularly
4. **Use managed databases** only if needed
5. **Monitor usage** - set up billing alerts

### Estimated Costs

**VPS Hosting:**
- Basic (2GB RAM): $5-6/month
- Recommended (4GB RAM): $12-15/month
- High-performance (8GB RAM): $24-30/month

**Additional Costs:**
- Domain name: ~$10/year (optional)
- Backups: Usually included or ~$1/month
- Bandwidth: Usually free (included in VPS)

## Support & Maintenance

### Regular Maintenance Tasks

**Daily:**
- Check logs for errors
- Monitor resource usage

**Weekly:**
- Review plugin performance
- Check backup integrity
- Update if needed

**Monthly:**
- Security updates
- Database optimization
- Cost review

### Getting Help

1. Check logs: `docker-compose logs agent`
2. Review documentation
3. Check plugin configurations
4. Test with simple messages first

## Next Steps

After successful deployment:

1. Test all core features
2. Enable additional plugins as needed
3. Set up monitoring and alerts
4. Configure automated backups
5. Customize for your use case

Your agent is now production-ready! 🎉
