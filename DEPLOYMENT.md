# KrishiSathi Production Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Setup](#docker-setup)
4. [Production Deployment](#production-deployment)
5. [Nginx Configuration](#nginx-configuration)
6. [HTTPS/SSL Setup](#httpssl-setup)
7. [Database Management](#database-management)
8. [Backup & Recovery](#backup--recovery)
9. [Monitoring & Health Checks](#monitoring--health-checks)
10. [Scaling Recommendations](#scaling-recommendations)
11. [Security Best Practices](#security-best-practices)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04 LTS or later (recommended for production)
- **CPU**: Minimum 2 cores (4+ cores recommended for production)
- **RAM**: Minimum 4GB (8GB+ for production)
- **Storage**: 20GB minimum (SSD recommended)
- **Docker**: 20.10 or later
- **Docker Compose**: 1.29 or later

### Required Software
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install -y docker-compose

# Install PostgreSQL client (for backup/restore)
sudo apt-get install -y postgresql-client

# Install Nginx (for reverse proxy)
sudo apt-get install -y nginx

# Install Git
sudo apt-get install -y git
```

### DNS Configuration
Set up DNS records pointing to your server:
```
A record: yourdomain.com -> YOUR_SERVER_IP
A record: www.yourdomain.com -> YOUR_SERVER_IP
A record: api.yourdomain.com -> YOUR_SERVER_IP
```

---

## Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/KRISHI_SATHI-VikasBeejBhandar.git
cd KRISHI_SATHI-VikasBeejBhandar
```

### 2. Setup Environment Variables
```bash
# Copy development environment
cp .env.development backend/.env

# For production simulation, copy production env
cp .env.production backend/.env
```

### 3. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (if using Alembic)
# alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### 5. Access Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

---

## Docker Setup

### 1. Generate SSL Certificates (for development)
```bash
# Navigate to project root
cd /path/to/KRISHI_SATHI-VikasBeejBhandar

# Generate self-signed certificates
chmod +x generate-ssl.sh
./generate-ssl.sh
```

### 2. Build Docker Images
```bash
# Build all images
docker compose build

# Or build specific services
docker compose build backend
docker compose build frontend
```

### 3. Start Services
```bash
# Start all services in background
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v
```

### 4. Verify Deployment
```bash
# Check service status
docker compose ps

# Check backend health
curl http://localhost:8000/api/health

# Check frontend
curl http://localhost:80

# Check database connection
docker compose exec postgres psql -U krishiuser -d krishisathi -c "SELECT 1"
```

### 5. Docker Compose Commands
```bash
# View specific service logs
docker compose logs -f backend

# Execute command in service
docker compose exec backend bash

# Rebuild single service
docker compose up -d --build backend

# Remove all stopped containers
docker system prune -a
```

---

## Production Deployment

### 1. Server Setup
```bash
# Connect to your production server
ssh ubuntu@YOUR_SERVER_IP

# Create application directory
sudo mkdir -p /app/krishisathi
sudo chown ubuntu:ubuntu /app/krishisathi
cd /app/krishisathi

# Clone repository
git clone https://github.com/yourusername/KRISHI_SATHI-VikasBeejBhandar.git .
```

### 2. Environment Configuration
```bash
# Create production environment file
cp .env.example .env.production

# Edit with your production values
nano .env.production
```

**Critical values to set:**
```env
# Database
DATABASE_URL=postgresql://krishiuser:STRONG_PASSWORD@postgres:5432/krishisathi
DB_PASSWORD=STRONG_PASSWORD

# Security
SECRET_KEY=GENERATE_NEW_SECRET_KEY
GEMINI_API_KEY=YOUR_API_KEY

# Domain
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
FRONTEND_URL=https://yourdomain.com
API_URL=https://api.yourdomain.com

# Email
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 3. Generate Strong Credentials
```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generate database password
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Pull Latest Images
```bash
# Pull Docker images
docker compose pull

# Or build from source
docker compose build --pull
```

### 5. Initialize Database
```bash
# Create database and run migrations
docker compose exec backend python -m alembic upgrade head

# Or if not using Alembic:
docker compose exec backend python -c "from app.database.db import Base, engine; Base.metadata.create_all(bind=engine)"

# Create initial data (if needed)
docker compose exec backend python -m app.scripts.seed_data
```

### 6. Start Services
```bash
# Start all services
docker compose up -d

# Verify services are running
docker compose ps

# Check logs
docker compose logs -f
```

### 7. Health Check
```bash
# Wait for services to start
sleep 10

# Check backend health
curl https://yourdomain.com/api/health

# Check frontend
curl https://yourdomain.com

# Check database
curl https://yourdomain.com/api/health | jq '.components.database'
```

---

## Nginx Configuration

### 1. Basic Nginx Setup
```bash
# Nginx configuration is included in docker-compose.yml
# Volumes mounted from ./nginx/

# Verify Nginx configuration
sudo docker compose exec nginx nginx -t

# Reload Nginx
sudo docker compose exec nginx nginx -s reload
```

### 2. Performance Tuning
Edit `nginx/nginx.conf`:
```nginx
# Increase worker processes
worker_processes 4;  # or auto

# Increase worker connections
events {
    worker_connections 4096;
}

# Enable gzip compression
gzip on;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript;
```

### 3. Caching Strategy
```nginx
# Browser caching for static assets
location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}

# API cache (short-lived)
location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 1m;
}
```

---

## HTTPS/SSL Setup

### 1. Let's Encrypt with Certbot

#### Initial Setup
```bash
# Stop Nginx temporarily
docker compose exec nginx nginx -s stop

# Install Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --standalone \
    -d yourdomain.com \
    -d www.yourdomain.com \
    -d api.yourdomain.com \
    --non-interactive \
    --agree-tos \
    -m admin@yourdomain.com

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/key.pem
sudo chown 1000:1000 ./nginx/ssl/*
```

#### Auto-Renewal
```bash
# Create renewal script
cat > /usr/local/bin/renew-certs.sh << 'EOF'
#!/bin/bash
cd /app/krishisathi

# Renew certificates
certbot renew --quiet --no-self-upgrade

# Copy to Docker volume
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/key.pem
sudo chown 1000:1000 ./nginx/ssl/*

# Reload Nginx
docker compose exec nginx nginx -s reload
EOF

chmod +x /usr/local/bin/renew-certs.sh

# Add to crontab (renew daily at 2 AM)
echo "0 2 * * * /usr/local/bin/renew-certs.sh" | sudo crontab -
```

### 2. Using docker-compose.prod.yml
```bash
# Deploy with Let's Encrypt setup
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Certbot container will automatically renew certificates
```

### 3. Force HTTPS
```nginx
# In nginx/conf.d/krishisathi.conf
# Redirect HTTP to HTTPS (already configured)
server {
    listen 80;
    return 301 https://$host$request_uri;
}
```

---

## Database Management

### 1. Backup Database
```bash
# Manual backup
./backend/scripts/backup-db.sh

# Scheduled backup (cron job)
# Edit crontab
crontab -e

# Add this line for daily backup at 2 AM
0 2 * * * /app/krishisathi/backend/scripts/backup-db.sh
```

### 2. Restore Database
```bash
# List available backups
ls -lah backups/

# Restore from backup
./backend/scripts/restore-db.sh backups/krishisathi_backup_20240101_120000.sql

# Or restore compressed backup
./backend/scripts/restore-db.sh backups/krishisathi_backup_20240101_120000.sql.gz
```

### 3. Database Maintenance
```bash
# Check database health
./backend/scripts/db-health-check.sh

# Vacuum (cleanup)
docker compose exec postgres vacuumdb -U krishiuser -d krishisathi -v

# Analyze (update statistics)
docker compose exec postgres analyzedb -U krishiuser -d krishisathi -v

# Reindex
docker compose exec postgres reindexdb -U krishiuser -d krishisathi -v
```

### 4. Database Monitoring
```bash
# Get database size
docker compose exec postgres psql -U krishiuser -d krishisathi -c \
    "SELECT pg_size_pretty(pg_database_size(current_database()));"

# List tables and their sizes
docker compose exec postgres psql -U krishiuser -d krishisathi -c \
    "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Check active connections
docker compose exec postgres psql -U krishiuser -d krishisathi -c \
    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database();"
```

---

## Backup & Recovery

### 1. Automated Backup Strategy
```yaml
# Backup Schedule (docker-compose.prod.yml)
- Daily full database backup at 2 AM
- Keep backups for 30 days
- Store on separate volume/NAS
- Log all backup operations
```

### 2. Multi-Level Backups
```bash
# Database backup
./backend/scripts/backup-db.sh

# Uploads backup
tar -czf backups/uploads_$(date +%Y%m%d_%H%M%S).tar.gz backend/app/uploads/

# Logs backup
tar -czf backups/logs_$(date +%Y%m%d_%H%M%S).tar.gz backend/logs/

# Docker volumes backup
docker run --rm \
    -v krishisathi_postgres_data:/data \
    -v $(pwd)/backups:/backup \
    alpine tar czf /backup/postgres_volume_$(date +%Y%m%d_%H%M%S).tar.gz /data
```

### 3. Disaster Recovery Procedure
```bash
# Step 1: Stop all services
docker compose stop

# Step 2: Restore database
./backend/scripts/restore-db.sh backups/krishisathi_backup_<timestamp>.sql.gz

# Step 3: Restore uploads (if corrupted)
tar -xzf backups/uploads_<timestamp>.tar.gz -C ./

# Step 4: Restart services
docker compose up -d

# Step 5: Verify
curl https://yourdomain.com/api/health
```

### 4. Offsite Backup (AWS S3 example)
```bash
#!/bin/bash
# scripts/backup-to-s3.sh

BACKUP_FILE="krishisathi_backup_$(date +%Y%m%d_%H%M%S).sql.gz"
BACKUP_DIR="backups"

# Create backup
./backend/scripts/backup-db.sh

# Upload to S3
aws s3 cp "$BACKUP_DIR/$BACKUP_FILE" s3://your-bucket/krishisathi-backups/ \
    --storage-class GLACIER_IR \
    --sse AES256

echo "Backup uploaded to S3: $BACKUP_FILE"
```

---

## Monitoring & Health Checks

### 1. Health Endpoints
```bash
# Overall health
curl https://yourdomain.com/api/health

# Readiness check (can handle requests?)
curl https://yourdomain.com/api/health/ready

# Liveness check (is running?)
curl https://yourdomain.com/api/health/live

# Parse JSON response
curl -s https://yourdomain.com/api/health | jq '.'
```

### 2. Log Monitoring
```bash
# View application logs
docker compose logs -f backend

# View error logs only
docker compose logs -f backend 2>&1 | grep ERROR

# View access logs
docker compose logs -f nginx

# View specific time range
docker compose logs --since 1h backend
```

### 3. Performance Monitoring
```bash
# Check container resource usage
docker stats

# Continuous monitoring
watch docker stats

# Historical data
docker compose exec backend tail -f logs/app.log

# Real-time log analysis
docker compose logs -f backend | grep -E "duration|error"
```

### 4. Alerts & Notifications
```bash
# Monitor health endpoint with simple script
#!/bin/bash
while true; do
    STATUS=$(curl -s https://yourdomain.com/api/health | jq -r '.status')
    if [ "$STATUS" != "healthy" ]; then
        # Send alert (email, Slack, etc.)
        curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK \
            -d '{"text":"⚠️ KrishiSathi health check failed: '$STATUS'"}'
    fi
    sleep 300  # Check every 5 minutes
done
```

---

## Scaling Recommendations

### 1. Horizontal Scaling (Multiple Servers)
```bash
# Use load balancer (AWS ELB, HAProxy, etc.)
# Deploy multiple backend instances
# Configure database replication

# Example HAProxy configuration
# upstream krishisathi_backend {
#     server backend1:8000 weight 5;
#     server backend2:8000 weight 5;
#     server backend3:8000 weight 5;
# }
```

### 2. Database Scaling
```bash
# Connection pooling
# docker-compose.yml backend service
DATABASE_URL=postgresql://user:pass@postgres:5432/krishisathi?pool_size=10&max_overflow=20

# Read replicas for high load
# PostgreSQL streaming replication setup
```

### 3. Caching Strategy
```bash
# Add Redis cache
# Update docker-compose.yml with Redis service
# Configure FastAPI with Redis caching
# Cache API responses, user sessions

# Example cache backend
# from fastapi_cache2 import FastAPICache2
# from fastapi_cache2.backends.redis import RedisBackend
# FastAPICache2.init(RedisBackend(redis_client), prefix="krishisathi")
```

### 4. CDN Integration
```bash
# Serve static assets from CDN
# Configure Nginx to serve from CloudFront/Cloudflare
# Reduce backend load significantly

# Update Nginx config
location ~* \.(js|css|png|jpg|jpeg|gif)$ {
    add_header Cache-Control "public, max-age=31536000, immutable";
    add_header X-CDN-Cache-Status $upstream_cache_status;
}
```

### 5. Load Testing
```bash
# Install load testing tool
sudo apt-get install -y apache2-utils

# Run load test
ab -n 10000 -c 100 https://yourdomain.com/api/health

# Using locust (Python)
pip install locust
# Create locustfile.py and run tests
```

---

## Security Best Practices

### 1. SSL/TLS
- [x] Use HTTPS everywhere
- [x] Enable HSTS header
- [x] Regular certificate updates
- [x] Strong cipher suites

### 2. Authentication & Authorization
- [x] Implement rate limiting
- [x] Use strong JWT tokens
- [x] Enforce CORS
- [x] Validate API requests

### 3. Data Protection
- [x] Encrypt sensitive data at rest
- [x] Use parameterized queries (prevent SQL injection)
- [x] Regular backups with encryption
- [x] Secure password storage (bcrypt)

### 4. Server Hardening
```bash
# Update system regularly
sudo apt-get update && sudo apt-get upgrade -y

# Enable firewall
sudo ufw enable
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443

# Disable root login
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Require key-based SSH authentication
sudo sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Restart SSH
sudo systemctl restart sshd
```

### 5. Container Security
```bash
# Run containers as non-root
# (already configured in Dockerfiles)

# Use read-only root filesystem where possible
# docker run --read-only ...

# Regularly scan images for vulnerabilities
docker scan krishisathi-backend:latest
```

---

## Troubleshooting

### 1. Container Issues
```bash
# Container not starting
docker compose logs backend
docker compose inspect backend

# Port already in use
sudo lsof -i :8000
kill -9 <PID>

# Out of memory
docker stats
docker system prune -a

# Container health check failing
docker compose exec backend curl http://localhost:8000/api/health
```

### 2. Database Issues
```bash
# Connection refused
docker compose logs postgres
docker compose exec postgres psql -U krishiuser -c "SELECT 1"

# Database locked
docker compose exec postgres ps aux | grep postgres

# Disk space
docker compose exec postgres du -sh /var/lib/postgresql/data
```

### 3. SSL/Certificate Issues
```bash
# Certificate expired
sudo certbot certificates

# Wrong certificate installed
curl -I https://yourdomain.com | grep Certificate

# Renewal failed
sudo certbot renew --dry-run
sudo certbot renew -vvv
```

### 4. Performance Issues
```bash
# Slow queries
docker compose exec backend tail -f logs/app.log | grep "duration"

# High CPU usage
docker stats
top

# High memory usage
docker inspect -f '{{.State.Pid}}' krishisathi_backend | xargs ps aux

# Slow database
docker compose exec postgres psql -U krishiuser -d krishisathi \
    -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### 5. Network Issues
```bash
# DNS resolution
docker compose exec backend nslookup postgres

# Service connectivity
docker compose exec backend curl http://nginx:80
docker compose exec backend curl http://backend:8000

# Port mapping
docker compose port backend 8000
docker compose port nginx 443
```

### 6. Getting Help
```bash
# Check logs
docker compose logs -f

# Detailed error information
docker compose logs backend --tail 100

# System information
docker version
docker compose version
uname -a

# Create support bundle
mkdir -p support-bundle
docker compose ps > support-bundle/services.txt
docker compose logs > support-bundle/logs.txt
docker system df > support-bundle/disk.txt
```

---

## Maintenance Schedule

### Daily
- Monitor health endpoints
- Review error logs
- Check disk space

### Weekly
- Database maintenance (vacuum, analyze)
- Review performance metrics
- Check backup status

### Monthly
- Security updates
- SSL certificate renewal (automatic)
- Performance optimization
- Database maintenance

### Quarterly
- Full system upgrade
- Security audit
- Disaster recovery test

---

## Support & Resources

- **Documentation**: https://github.com/yourusername/KRISHI_SATHI-VikasBeejBhandar/wiki
- **Issues**: https://github.com/yourusername/KRISHI_SATHI-VikasBeejBhandar/issues
- **Email**: support@yourdomain.com
- **Emergency**: emergency@yourdomain.com

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Maintained By**: DevOps Team
