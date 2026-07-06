# Production Deployment Checklist

## Pre-Deployment

### Infrastructure
- [ ] Cloud provider account setup (AWS, Azure, DigitalOcean, etc.)
- [ ] Server provisioned and accessible
- [ ] SSH key configured and tested
- [ ] Firewall rules configured (ports 80, 443, 22)
- [ ] Storage and backup infrastructure ready
- [ ] DNS records configured and verified
- [ ] CDN setup (optional but recommended)

### Security
- [ ] Secrets securely generated (SECRET_KEY, DB_PASSWORD, etc.)
- [ ] SSL/TLS certificate obtained (Let's Encrypt recommended)
- [ ] SSL certificate paths verified
- [ ] CORS origins properly configured
- [ ] API rate limiting configured
- [ ] Security headers enabled
- [ ] Database credentials changed from defaults
- [ ] Admin credentials changed from defaults

### Environment
- [ ] .env.production created with all values
- [ ] All required environment variables set
- [ ] No hardcoded secrets in code
- [ ] LOG_LEVEL set to INFO or WARNING
- [ ] API documentation disabled in production (docs_url=None)
- [ ] Debug mode disabled in FastAPI
- [ ] ENVIRONMENT variable set to "production"

### Database
- [ ] PostgreSQL version confirmed compatible
- [ ] Database user created with strong password
- [ ] Database permissions configured (least privilege)
- [ ] Backup storage location confirmed
- [ ] Backup scripts tested
- [ ] Database restoration tested from backup
- [ ] Connection pooling configured
- [ ] Character encoding set to UTF-8

### Networking
- [ ] DNS pointing to server
- [ ] Nginx reverse proxy configured
- [ ] SSL termination working
- [ ] HTTP to HTTPS redirect configured
- [ ] API endpoints accessible
- [ ] All services on same network (docker)
- [ ] Port mappings verified

---

## Deployment

### Build & Push
- [ ] Docker images built successfully
- [ ] Image sizes optimized (< 500MB for backend, < 300MB for frontend)
- [ ] Images tagged with version number
- [ ] Images pushed to registry (if using remote registry)
- [ ] Docker Compose file verified
- [ ] docker-compose.prod.yml created and tested

### Services Startup
- [ ] PostgreSQL started and initialized
- [ ] Backend service started and healthy
- [ ] Frontend service started and accessible
- [ ] Nginx service started and responding
- [ ] All services running without errors
- [ ] Services set to auto-restart on failure

### Health Checks
- [ ] Backend /api/health endpoint responding
- [ ] Database connectivity verified
- [ ] Frontend loading without errors
- [ ] API endpoints returning expected responses
- [ ] System resources within acceptable limits
- [ ] No error messages in logs

### Initial Data
- [ ] Database schema created
- [ ] Initial migrations applied (if using Alembic)
- [ ] Seed data loaded (if applicable)
- [ ] Test user created for verification
- [ ] Admin account created with strong password

---

## Post-Deployment

### Verification
- [ ] Frontend loads in browser
- [ ] API documentation accessible (if enabled)
- [ ] Login functionality working
- [ ] Core features tested manually
- [ ] File uploads working
- [ ] All routers initialized successfully
- [ ] WebSocket connections working (if applicable)

### Monitoring Setup
- [ ] Health check monitoring configured
- [ ] Log aggregation enabled
- [ ] Error tracking enabled (Sentry, etc.)
- [ ] Performance monitoring enabled
- [ ] Uptime monitoring configured
- [ ] Alerts configured for critical issues
- [ ] Dashboard created for monitoring

### Backups
- [ ] Automated backup schedule configured
- [ ] First backup completed successfully
- [ ] Backup storage verified
- [ ] Restore procedure tested
- [ ] Backup retention policy configured
- [ ] Offsite backup configured (recommended)
- [ ] Backup monitoring enabled

### Security Verification
- [ ] HTTPS working and enforced
- [ ] Security headers present in responses
- [ ] CORS properly configured
- [ ] Rate limiting working
- [ ] SQL injection prevention verified
- [ ] XSS protection verified
- [ ] CSRF protection enabled
- [ ] No sensitive data in logs

### Performance Baseline
- [ ] API response times recorded
- [ ] Database query performance checked
- [ ] Cache effectiveness verified
- [ ] CPU usage at idle recorded
- [ ] Memory usage at idle recorded
- [ ] Disk usage baseline recorded
- [ ] Load testing results recorded

### SSL/Certificate
- [ ] Certificate installed and valid
- [ ] Certificate expiry monitored
- [ ] Auto-renewal configured
- [ ] Certificate chain complete
- [ ] HSTS header enabled
- [ ] Certificate validation working

---

## 7-Day Post-Deployment

- [ ] Monitor all systems continuously
- [ ] Review error logs for patterns
- [ ] Check backup completion status
- [ ] Verify no unexpected restarts
- [ ] Monitor database growth
- [ ] Review security logs
- [ ] Performance metrics stable
- [ ] User feedback collected

---

## 30-Day Post-Deployment

- [ ] Full system health review
- [ ] Database maintenance (vacuum, analyze)
- [ ] Backup restoration test
- [ ] Security audit
- [ ] Performance optimization review
- [ ] Capacity planning assessment
- [ ] Documentation updates
- [ ] Team knowledge transfer complete

---

## Ongoing Maintenance

### Daily
- [ ] Monitor health endpoints
- [ ] Review critical error logs
- [ ] Check disk space availability
- [ ] Verify backup completion

### Weekly
- [ ] Review performance metrics
- [ ] Check resource utilization
- [ ] Security update checks
- [ ] Database maintenance

### Monthly
- [ ] Security audit
- [ ] Performance optimization
- [ ] Backup restoration test
- [ ] Capacity planning review
- [ ] Certificate renewal check
- [ ] Team training updates

### Quarterly
- [ ] Major version updates
- [ ] Full security audit
- [ ] Disaster recovery test
- [ ] Performance tuning
- [ ] Compliance review

### Annually
- [ ] Full system audit
- [ ] Security penetration test
- [ ] Architecture review
- [ ] Capacity planning
- [ ] Business continuity update

---

## Emergency Procedures

### Service Down
- [ ] Check service status: `docker compose ps`
- [ ] Review logs: `docker compose logs -f`
- [ ] Restart service: `docker compose restart <service>`
- [ ] If persists, restart all: `docker compose restart`
- [ ] Check database: `./backend/scripts/db-health-check.sh`
- [ ] Notify stakeholders

### Database Issues
- [ ] Check connections: `docker compose exec postgres psql -c "SELECT * FROM pg_stat_activity;"`
- [ ] Kill hung processes if needed
- [ ] Check disk space
- [ ] Restore from backup if corrupted
- [ ] Review PostgreSQL logs

### Security Breach
- [ ] Isolate affected systems
- [ ] Review access logs
- [ ] Check for unauthorized changes
- [ ] Rotate credentials
- [ ] Deploy security patches
- [ ] Notify users if data affected

### SSL Certificate Issues
- [ ] Check certificate: `openssl s_client -connect yourdomain.com:443`
- [ ] Verify expiry: `sudo certbot certificates`
- [ ] Renew if needed: `sudo certbot renew`
- [ ] Restart Nginx: `docker compose exec nginx nginx -s reload`

---

## Rollback Procedure

### Minor Issue
```bash
# Stop affected service
docker compose stop <service>

# Revert to previous image
docker compose pull
docker compose up -d <service>
```

### Database Rollback
```bash
# Stop services
docker compose stop backend

# Restore database
./backend/scripts/restore-db.sh backups/<previous-backup>

# Start services
docker compose start backend
```

### Full Rollback
```bash
# Stop all services
docker compose down

# Restore database
./backend/scripts/restore-db.sh backups/<previous-backup>

# Restore previous code
git checkout <previous-commit>

# Restart everything
docker compose build
docker compose up -d
```

---

## Documentation

### Required Documentation
- [ ] Deployment guide (DEPLOYMENT.md)
- [ ] Architecture overview
- [ ] Admin manual
- [ ] Runbook for common tasks
- [ ] Disaster recovery procedure
- [ ] On-call guide
- [ ] Security guidelines

### Team Knowledge
- [ ] All team members trained on deployment
- [ ] Access credentials properly documented
- [ ] Contact information updated
- [ ] Escalation procedures documented
- [ ] Decision log maintained

---

## Sign-Off

**Prepared By**: ________________________  Date: _________

**Reviewed By**: ________________________  Date: _________

**Approved By**: ________________________  Date: _________

**Deployed By**: ________________________  Date: _________

**Verified By**: ________________________  Date: _________

---

## Notes

```
[Space for additional notes and observations]



```

---

**This checklist must be completed and signed off before production deployment.**

For detailed instructions, see: [DEPLOYMENT.md](./DEPLOYMENT.md)
