# KrishiSathi-VikasBeejBhandar - Production Ready

> **Agricultural E-commerce Platform** - Production-grade deployment with Docker, Kubernetes-ready architecture, and enterprise-level security.

## Quick Links
- 📖 [Full Deployment Guide](./DEPLOYMENT.md)
- 🐳 [Docker Documentation](./docker-compose.yml)
- 🔐 [SSL/HTTPS Setup](./certbot.ini)
- 📊 [Architecture Overview](#architecture)
- 🚀 [Quick Start](#quick-start)

---

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Docker Deployment](#docker-deployment)
- [Production Setup](#production-setup)
- [API Documentation](#api-documentation)
- [Security Features](#security-features)
- [Performance Optimization](#performance-optimization)
- [Monitoring & Logging](#monitoring--logging)
- [Contributing](#contributing)
- [Support](#support)

---

## Features

### ✅ Production Ready
- Multi-stage Docker builds for optimized images
- Docker Compose for orchestration
- Nginx reverse proxy with SSL/HTTPS
- PostgreSQL database with backups
- Structured JSON logging
- Health checks and monitoring
- Rate limiting and security headers
- Global exception handling

### 🎯 Core Functionality
- **Authentication**: JWT-based with role management
- **E-commerce**: Product catalog and ordering system
- **AI Assistant**: Gemini API integration
- **RAG**: Document retrieval and augmented generation
- **Voice**: Speech-to-text and text-to-speech
- **Scanner**: Product barcode/QR code scanning
- **Analytics**: User behavior and sales analytics
- **Weather**: Real-time weather integration
- **Farm Planning**: Crop planning and calendar
- **Admin Dashboard**: Comprehensive management interface

### 🔒 Security
- SQL injection prevention
- XSS protection
- CSRF protection
- CORS configuration
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Input validation and sanitization
- File upload validation
- Rate limiting (authentication: 10 req/min, API: 100 req/min)

### 📊 Monitoring
- Comprehensive health checks (`/api/health`)
- Readiness probes (`/api/health/ready`)
- Liveness probes (`/api/health/live`)
- Component-level monitoring (database, system, AI, storage)
- Access and error logging
- Performance metrics
- Request tracking (X-Request-ID)

### 🚀 Performance
- Gzip compression
- Static asset caching (30 days for production)
- API response caching
- Database connection pooling
- Multi-worker UVICORN setup
- Nginx request buffering
- Image optimization

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client (Browser)                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┴────────────────┐
        │                                │
┌───────▼────────────────────────┐  ┌──▼────────┐
│   Nginx (Reverse Proxy)        │  │ Logs      │
│  - SSL/TLS Termination         │  │ Collector │
│  - Compression (gzip)          │  └───────────┘
│  - Caching                     │
│  - Rate Limiting               │
└───────┬────────────────────────┘
        │
   ┌────┴──────┬──────────────┐
   │            │              │
┌──▼──────┐ ┌──▼──────┐ ┌────▼────┐
│Frontend │ │Backend  │ │ Storage  │
│React    │ │FastAPI  │ │Uploads   │
└─────────┘ └──┬──────┘ └─────────┘
              │
         ┌────▼─────────┐
         │ PostgreSQL   │
         │ Database     │
         │ - Tables     │
         │ - Backups    │
         └──────────────┘
```

### Components
1. **Frontend** (React + TypeScript)
   - Vite build system
   - Responsive UI with Tailwind CSS
   - Real-time updates

2. **Backend** (FastAPI)
   - RESTful API
   - Async/await support
   - Automatic OpenAPI documentation

3. **Database** (PostgreSQL)
   - ACID compliance
   - Full-text search
   - JSON support

4. **Reverse Proxy** (Nginx)
   - Load balancing
   - SSL/TLS termination
   - Response compression
   - Caching

---

## Prerequisites

### System Requirements
```
OS: Ubuntu 20.04+ (Linux) or Docker Desktop (macOS/Windows)
CPU: 2 cores minimum (4+ recommended)
RAM: 4GB minimum (8GB+ recommended)
Disk: 20GB minimum (SSD recommended)
```

### Required Software
```bash
Docker ≥ 20.10
Docker Compose ≥ 1.29
Git ≥ 2.25
PostgreSQL client ≥ 12 (optional, for local DB access)
```

### Installation
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git

# Add current user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

---

## Quick Start

### 1. Development (Local)
```bash
# Clone repository
git clone https://github.com/yourusername/KRISHI_SATHI-VikasBeejBhandar.git
cd KRISHI_SATHI-VikasBeejBhandar

# Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Setup frontend
cd frontend
npm install
cd ..

# Copy environment
cp .env.development backend/.env

# Start services
cd backend && uvicorn app.main:app --reload &
cd ../frontend && npm run dev &

# Access
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

### 2. Docker (Recommended)
```bash
# Copy environment
cp .env.example .env.development

# Generate SSL (development)
chmod +x generate-ssl.sh
./generate-ssl.sh

# Build and start
docker compose up -d

# Verify
docker compose ps
docker compose logs -f

# Access
# Frontend: https://localhost
# Backend: https://localhost/api
# Health: https://localhost/api/health
```

### 3. Production
```bash
# Copy and configure production environment
cp .env.example .env.production
nano .env.production  # Edit with actual values

# Generate SSL (Let's Encrypt)
sudo certbot certonly --standalone -d yourdomain.com

# Deploy
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Monitor
docker compose logs -f
curl https://yourdomain.com/api/health
```

---

## Project Structure

```
KRISHI_SATHI-VikasBeejBhandar/
├── backend/                         # FastAPI backend
│   ├── app/
│   │   ├── core/                   # Configuration & security
│   │   │   ├── config.py          # Environment & settings
│   │   │   ├── logging_config.py  # Structured logging
│   │   │   ├── health.py          # Health checks
│   │   │   ├── middleware.py      # Request logging
│   │   │   ├── exceptions.py      # Error handling
│   │   │   ├── security_utils.py  # Security utilities
│   │   │   └── security.py        # JWT & auth
│   │   ├── database/              # Database layer
│   │   ├── models/                # ORM models
│   │   ├── routers/               # API endpoints
│   │   ├── schemas/               # Pydantic schemas
│   │   ├── services/              # Business logic
│   │   ├── uploads/               # File storage
│   │   ├── logs/                  # Application logs
│   │   └── main.py               # FastAPI app
│   ├── scripts/
│   │   ├── backup-db.sh          # Database backup
│   │   ├── restore-db.sh         # Database restore
│   │   ├── db-health-check.sh    # Health check
│   │   └── init-db.sql           # DB initialization
│   ├── requirements.txt           # Python dependencies
│   ├── Dockerfile                # Docker image
│   └── .dockerignore
│
├── frontend/                       # React frontend
│   ├── src/
│   │   ├── api/                  # API client
│   │   ├── components/           # React components
│   │   ├── pages/               # Page components
│   │   ├── hooks/               # Custom hooks
│   │   ├── context/             # Context API
│   │   ├── types/               # TypeScript types
│   │   ├── utils/               # Utilities
│   │   ├── App.tsx              # Main app
│   │   └── main.tsx             # Entry point
│   ├── package.json             # Node dependencies
│   ├── vite.config.ts           # Vite configuration
│   ├── tsconfig.json            # TypeScript config
│   ├── Dockerfile               # Docker image
│   └── .dockerignore
│
├── nginx/                         # Reverse proxy config
│   ├── nginx.conf               # Main configuration
│   ├── conf.d/
│   │   └── krishisathi.conf    # App configuration
│   └── ssl/                     # SSL certificates
│
├── .github/workflows/            # CI/CD pipelines
│   ├── ci.yml                  # Build & test
│   └── deploy.yml              # Deployment
│
├── docker-compose.yml            # Service orchestration
├── docker-compose.prod.yml       # Production overrides
├── .env.example                 # Environment template
├── .env.development             # Development env
├── .env.production              # Production env
├── .env.testing                 # Testing env
├── generate-ssl.sh              # SSL generation
├── certbot.ini                  # Let's Encrypt config
├── DEPLOYMENT.md                # Full deployment guide
├── README.md                    # This file
└── LICENSE
```

---

## Environment Variables

### Development
```bash
DATABASE_URL=postgresql://krishiuser:password@localhost/krishisathi
SECRET_KEY=dev-secret-key-min-32-chars
GEMINI_API_KEY=your-gemini-api-key
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### Production
```bash
DATABASE_URL=postgresql://krishiuser:secure_password@postgres:5432/krishisathi
SECRET_KEY=generate_new_secret_key_32_chars_min
GEMINI_API_KEY=production-gemini-api-key
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
FRONTEND_URL=https://yourdomain.com
ENVIRONMENT=production
LOG_LEVEL=INFO
ENABLE_HSTS=true
ENABLE_CSP=true
```

See [`.env.example`](./.env.example) for all available variables.

---

## Docker Deployment

### Build Images
```bash
# All services
docker compose build

# Single service
docker compose build backend
docker compose build frontend
docker compose build nginx

# With build args
docker compose build --build-arg BUILDKIT_INLINE_CACHE=1
```

### Start Services
```bash
# Background
docker compose up -d

# Foreground (see logs)
docker compose up

# Specific service
docker compose up -d backend

# Rebuild on start
docker compose up -d --build
```

### Manage Services
```bash
# Status
docker compose ps

# Logs
docker compose logs -f backend
docker compose logs --tail 50 nginx
docker compose logs -f --since 1h

# Execute commands
docker compose exec backend bash
docker compose exec postgres psql -U krishiuser

# Restart
docker compose restart backend
docker compose stop && docker compose start

# Remove
docker compose down
docker compose down -v  # Include volumes
```

### Health Checks
```bash
# Check services
docker compose ps

# Service logs
docker compose logs postgres

# Direct health check
curl http://localhost:8000/api/health
curl http://localhost/api/health

# Database connection
docker compose exec postgres psql -U krishiuser -c "SELECT 1"
```

---

## Production Setup

### 1. Server Preparation
```bash
ssh ubuntu@your-server-ip

# Create application directory
sudo mkdir -p /app/krishisathi
sudo chown ubuntu:ubuntu /app/krishisathi

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh | sudo sh

# Clone repository
cd /app/krishisathi
git clone https://github.com/yourusername/KRISHI_SATHI-VikasBeejBhandar.git .
```

### 2. Environment Setup
```bash
# Create production environment
cp .env.example .env.production

# Generate secure credentials
python3 -c "import secrets; print(secrets.token_hex(32))"

# Edit with production values
nano .env.production
```

### 3. SSL Certificate Setup
```bash
# Using Let's Encrypt
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy to project
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/key.pem
sudo chown 1000:1000 ./nginx/ssl/*
```

### 4. Deploy
```bash
# Pull latest images
docker compose pull

# Build locally if needed
docker compose build --pull

# Start services
docker compose up -d

# Verify
docker compose ps
sleep 10
curl https://yourdomain.com/api/health
```

### 5. Backup Setup
```bash
# Automated daily backups
chmod +x backend/scripts/backup-db.sh

# Add to crontab
crontab -e
# 0 2 * * * /app/krishisathi/backend/scripts/backup-db.sh
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for comprehensive production guide.

---

## API Documentation

### Health Check
```bash
# Overall health
GET /api/health

# Response
{
  "status": "healthy",
  "environment": "production",
  "components": {
    "database": {"status": "healthy", ...},
    "system": {"status": "healthy", ...},
    "ai_service": {"status": "healthy", ...},
    "storage": {"status": "healthy", ...}
  }
}
```

### Authentication
```bash
# Register
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "User Name"
}

# Login
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Available Endpoints
- **Auth**: `/api/auth/` - Login, register, token refresh
- **Products**: `/api/products/` - CRUD operations
- **Orders**: `/api/orders/` - Order management
- **Scanner**: `/api/scanner/` - Product scanning
- **Assistant**: `/api/assistant/` - AI assistant
- **RAG**: `/api/rag/` - Document retrieval
- **Voice**: `/api/voice/` - Speech processing
- **Analytics**: `/api/analytics/` - Analytics data
- **Farm Planner**: `/api/farm-plan/` - Crop planning
- **Knowledge**: `/api/knowledge/` - Knowledge base

### API Documentation
```
Development: http://localhost:8000/api/docs
Production: https://yourdomain.com/api/docs (if enabled)
```

---

## Security Features

### Built-In Security
- ✅ **HTTPS/TLS**: Enforced via Nginx
- ✅ **JWT Authentication**: Token-based auth
- ✅ **CORS**: Production-safe origins
- ✅ **Rate Limiting**: 100 req/min (API), 10 req/min (auth)
- ✅ **Security Headers**: HSTS, CSP, X-Frame-Options, etc.
- ✅ **SQL Injection**: Parameterized queries via SQLAlchemy
- ✅ **XSS Protection**: Input sanitization
- ✅ **CSRF Protection**: Token validation
- ✅ **Input Validation**: Pydantic schemas
- ✅ **File Upload Validation**: Extension & size checks
- ✅ **Secrets Management**: Environment variables only
- ✅ **Logging**: Structured JSON logs, no sensitive data

### Security Checklist
```
Pre-Deployment:
☑ Generate new SECRET_KEY
☑ Set strong database password
☑ Configure CORS origins
☑ Enable HTTPS certificate
☑ Review environment variables
☑ Set LOG_LEVEL to INFO (production)

Post-Deployment:
☑ Verify HTTPS redirect
☑ Test rate limiting
☑ Check security headers
☑ Monitor access logs
☑ Setup alerts
☑ Regular backups
```

---

## Performance Optimization

### Caching Strategy
```
Static Assets: 30 days (browser cache)
API Responses: 1-5 minutes (server cache)
Database Queries: Connection pooling
```

### Compression
```
Gzip: Enabled for text/JSON content
Static Files: Pre-compressed in CDN
Images: Optimized via frontend build
```

### Database
```
Connection Pool: 10-20 connections
Query Optimization: Indexed foreign keys
Maintenance: Vacuum daily, analyze weekly
```

### Load Balancing
```
Nginx: Round-robin to multiple backends
Health Checks: Every 30 seconds
Failover: Automatic to healthy instances
```

### Benchmarks (Local Development)
```
Frontend Build Time: ~30 seconds
Backend Startup: ~5 seconds
Database Init: ~2 seconds
API Response Time: <100ms (avg)
```

---

## Monitoring & Logging

### Log Files
```
Application: logs/app.log
Errors: logs/error.log
Access: logs/access.log
AI Services: logs/ai.log
Scanner: logs/scanner.log
```

### Log Format
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "app.routers.products",
  "message": "Product retrieved",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 123,
  "duration_ms": 45
}
```

### Monitoring Commands
```bash
# Real-time logs
docker compose logs -f

# Error logs only
docker compose logs backend 2>&1 | grep ERROR

# Performance metrics
docker compose exec backend tail -f logs/app.log | grep duration

# Health status
curl https://yourdomain.com/api/health | jq '.status'

# System resources
docker stats
```

---

## Database Management

### Backup
```bash
# Manual backup
./backend/scripts/backup-db.sh

# Lists backups
ls -lah backups/

# Automated backup (cron)
# 0 2 * * * /app/krishisathi/backend/scripts/backup-db.sh
```

### Restore
```bash
# Restore from backup
./backend/scripts/restore-db.sh backups/krishisathi_backup_20240115_020000.sql.gz
```

### Maintenance
```bash
# Health check
./backend/scripts/db-health-check.sh

# Vacuum
docker compose exec postgres vacuumdb -U krishiuser -d krishisathi

# Analyze
docker compose exec postgres analyzedb -U krishiuser -d krishisathi
```

---

## Troubleshooting

### Common Issues

**Services not starting**
```bash
docker compose logs
docker compose up --build
```

**Database connection failed**
```bash
docker compose ps
docker compose logs postgres
docker compose exec postgres psql -U krishiuser
```

**High CPU/Memory usage**
```bash
docker stats
docker compose exec backend ps aux
```

**SSL certificate errors**
```bash
docker compose exec nginx nginx -t
docker compose logs nginx
sudo certbot certificates
```

See [DEPLOYMENT.md](./DEPLOYMENT.md#troubleshooting) for detailed troubleshooting guide.

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Style
- Python: PEP 8 (Black formatter)
- TypeScript: ESLint configuration
- Commits: Conventional commits format

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Support

- **Documentation**: [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/KRISHI_SATHI-VikasBeejBhandar/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/KRISHI_SATHI-VikasBeejBhandar/discussions)
- **Email**: support@krishisathi.com

---

## Screenshots

### Frontend
- Admin Dashboard
- Product Catalog
- Order Management
- User Profile
- Analytics
- Weather Dashboard
- Farm Planner

### Backend
- API Documentation (Swagger/OpenAPI)
- Comprehensive Logging
- Health Dashboard
- Monitoring Metrics

---

**Version**: 1.0.0 (Production Ready)  
**Last Updated**: 2024  
**Maintainers**: DevOps Team

---

### Quick Commands Reference

```bash
# Development
npm run dev                    # Start frontend
uvicorn app.main:app --reload # Start backend

# Docker
docker compose up -d           # Start all services
docker compose logs -f         # View logs
docker compose down            # Stop all services

# Database
./backend/scripts/backup-db.sh # Backup database
./backend/scripts/restore-db.sh backups/<file> # Restore

# Deployment
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
docker compose ps              # Check status
curl https://yourdomain.com/api/health  # Health check
```

**Ready to deploy? Start with [DEPLOYMENT.md](./DEPLOYMENT.md)** 🚀
