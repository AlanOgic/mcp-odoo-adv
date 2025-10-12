# Coolify Git Repository Deployment - Complete Summary

This document provides a complete summary of the Coolify deployment setup for the Odoo MCP Server Advanced project.

---

## What Was Created

### 1. Docker Compose Configuration for Coolify
**File**: `docker-compose.coolify.yml`

- ✅ Optimized for Coolify deployment
- ✅ Pre-configured health checks
- ✅ Resource limits (CPU: 1.0, Memory: 512M)
- ✅ Persistent log volumes
- ✅ Two services: `odoo-mcp-http` (default) and `odoo-mcp-sse` (optional)
- ✅ Coolify-specific labels and network configuration

### 2. Coolify Configuration Metadata
**File**: `coolify.json`

- ✅ Service definitions with all parameters
- ✅ Environment variable documentation (required/optional)
- ✅ Health check configurations
- ✅ Volume mappings
- ✅ Resource limits
- ✅ Security recommendations
- ✅ Quick start guide in JSON format

### 3. Comprehensive Deployment Guide
**File**: `DOCS/COOLIFY.md` (950+ lines)

Complete guide covering:
- ✅ 5-minute quick start
- ✅ Prerequisites and requirements
- ✅ Step-by-step Git Repository deployment
- ✅ Environment variable configuration
- ✅ Port and domain configuration
- ✅ Monitoring and troubleshooting
- ✅ Security best practices
- ✅ Advanced configuration (multi-env, scaling, webhooks)
- ✅ Production checklist

### 4. Quick Reference Guide
**File**: `COOLIFY_QUICKSTART.md`

- ✅ Condensed 5-minute deployment guide
- ✅ Quick configuration tables
- ✅ Verification steps
- ✅ Common issues and solutions
- ✅ Security checklist

### 5. Updated Documentation
**File**: `README.md`

- ✅ Added COOLIFY.md to documentation section
- ✅ Listed as #4 in "New to Odoo MCP Server?" guide

### 6. Bug Fix
**File**: `Dockerfile`

- ✅ Fixed Python version from 3.14 (doesn't exist) to 3.12

---

## Deployment Architecture

### Git Repository Deployment Flow

```
GitHub Repository (mcp-odoo-adv)
         ↓
    Coolify Server
         ↓
   Git Clone & Build
         ↓
   Docker Compose Build
         ↓
   Create Containers
   (odoo-mcp-http:8008)
         ↓
   Health Checks
         ↓
    Deploy Success
         ↓
   Auto-Proxy via Coolify
```

### Why Git Repository Deployment?

**Advantages:**
- ✅ No Docker Hub dependency (no registry errors)
- ✅ Automatic builds from source
- ✅ Full control over configuration
- ✅ Easy updates via Git commits
- ✅ Version control for all changes
- ✅ Webhook auto-deploy support

**Disadvantages:**
- ⚠️ Longer initial build time (2-3 minutes vs <1 minute for pre-built images)
- ⚠️ Requires Git repository access

---

## Complete Deployment Steps

### Step 1: Create Application in Coolify

```
Coolify Dashboard → + New Resource → Application → Git Repository
```

### Step 2: Configure Git Repository

```yaml
Repository URL: https://github.com/AlanOgic/mcp-odoo-adv
Branch: master
Build Pack: Docker Compose
Compose File: docker-compose.coolify.yml
Service: odoo-mcp-http
```

### Step 3: Set Environment Variables

**Required (in Coolify UI):**
```bash
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password  # Mark as "Secret"
```

**Recommended for Odoo 19+:**
```bash
ODOO_API_VERSION=json-2
ODOO_API_KEY=your-api-key  # Replaces ODOO_PASSWORD
```

### Step 4: Configure Port

```
Internal Port: 8008
Protocol: HTTP
Public Port: Enable (auto-assigned or custom)
```

### Step 5: Optional - Add Domain

```
Domain: mcp.yourdomain.com
SSL: Enable (Let's Encrypt)
```

### Step 6: Deploy

```
Click "Deploy" → Monitor logs → Wait for "Deployment successful"
```

### Step 7: Verify

**Health Check:**
```bash
curl http://your-coolify-domain:8008/health
```

**MCP Endpoint:**
```bash
curl -X POST http://your-coolify-domain:8008/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
```

---

## File Configuration Details

### docker-compose.coolify.yml

**Key Features:**

```yaml
services:
  odoo-mcp-http:
    build:
      context: .
      dockerfile: Dockerfile.http
      args:
        PYTHON_VERSION: ${PYTHON_VERSION:-3.12}

    ports:
      - "${HTTP_PORT:-8008}:8008"

    environment:
      # All Odoo connection variables
      ODOO_URL: ${ODOO_URL}
      ODOO_DB: ${ODOO_DB}
      # ... etc

    volumes:
      - logs-http:/app/logs  # Persistent logs

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8008/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    restart: unless-stopped

    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M

    labels:
      - "coolify.managed=true"
      - "coolify.service=odoo-mcp-http"
```

**Optional SSE Service:**
- Enabled via `COMPOSE_PROFILES=sse` environment variable
- Or deployed as separate Coolify application
- Port 8009

### coolify.json

**Metadata Structure:**

```json
{
  "name": "Odoo MCP Server",
  "services": {
    "odoo-mcp-http": {
      "environment_variables": {
        "required": [...],
        "optional": [...]
      },
      "health_check": {...},
      "resources": {...}
    }
  },
  "quickstart": {
    "steps": [...]
  }
}
```

---

## Auto-Deploy with Git Webhooks

### Setup

1. **Get webhook URL from Coolify:**
   ```
   Application → Settings → Webhooks → Copy URL
   ```

2. **Configure in GitHub:**
   ```
   Repository → Settings → Webhooks → Add webhook
   Payload URL: <coolify-webhook-url>
   Content type: application/json
   Events: Push events
   ```

3. **Automatic deployment on push:**
   ```bash
   git commit -am "Update configuration"
   git push  # Triggers automatic rebuild in Coolify
   ```

---

## Monitoring & Logs

### Coolify Dashboard

```
Application → Logs → Container Logs (real-time)
Application → Status → Health Check Status
```

### Container Logs

```bash
# SSH to Coolify server
docker compose -f /path/to/deployment/docker-compose.yml logs -f odoo-mcp-http
```

### Application Logs

```bash
# Inside container
docker exec -it <container-id> tail -f /app/logs/mcp_server_*.log
```

### Log Volumes

```bash
# View volume location
docker volume inspect <project>_logs-http

# Backup logs
docker run --rm -v <project>_logs-http:/logs \
  -v $(pwd):/backup alpine \
  tar czf /backup/logs-backup.tar.gz /logs
```

---

## Security Configuration

### Production Checklist

- [ ] Use ODOO_API_KEY instead of ODOO_PASSWORD (Odoo 19+)
- [ ] Mark ODOO_PASSWORD as "Secret" in Coolify
- [ ] Enable SSL/TLS with Let's Encrypt
- [ ] Set DEBUG=0
- [ ] Configure rate limiting in Coolify proxy
- [ ] Set up log monitoring and alerts
- [ ] Configure resource limits (CPU/memory)
- [ ] Restrict network access (private network or auth)
- [ ] Test health checks
- [ ] Set up automated backups
- [ ] Configure monitoring (e.g., UptimeRobot)

### SSL/TLS Configuration

**In Coolify:**
```
Application → Domains → Add Domain → Enable SSL
```

Coolify automatically provisions Let's Encrypt certificates.

### Rate Limiting

**In Coolify proxy:**
```
Application → Advanced → Rate Limiting
Requests per minute: 100
Burst: 20
```

---

## Multi-Environment Deployment

### Development Environment

```yaml
Application: odoo-mcp-dev
Environment:
  ODOO_URL: https://dev.odoo.example.com
  ODOO_DB: dev-database
  DEBUG: 1
```

### Staging Environment

```yaml
Application: odoo-mcp-staging
Environment:
  ODOO_URL: https://staging.odoo.example.com
  ODOO_DB: staging-database
  DEBUG: 0
```

### Production Environment

```yaml
Application: odoo-mcp-prod
Environment:
  ODOO_URL: https://odoo.example.com
  ODOO_DB: production-database
  DEBUG: 0
  ODOO_API_VERSION: json-2
  ODOO_API_KEY: ${SECRET_API_KEY}
```

---

## Troubleshooting

### Build Failures

**Common Causes:**
- Insufficient disk space
- Network connectivity issues
- Dockerfile.http not found
- Python version incompatibility

**Solutions:**
```bash
# Check disk space
df -h

# Check build logs in Coolify
Application → Logs → Build Logs

# Verify Dockerfile exists
git ls-files Dockerfile.http
```

### Connection Errors

**Common Causes:**
- Incorrect ODOO_URL
- Network firewall blocking Coolify → Odoo
- Invalid credentials
- SSL verification issues

**Solutions:**
```bash
# Test from Coolify server
curl -I https://your-odoo-instance.com

# Disable SSL verification (not recommended for prod)
ODOO_VERIFY_SSL=0

# Check credentials
docker exec -it <container-id> python3 -c "
from odoo_mcp.odoo_client import get_odoo_client
client = get_odoo_client()
print('Connected:', client.uid is not None)
"
```

### Health Check Failures

**Common Causes:**
- Odoo connection timeout
- Application startup time exceeds start_period
- Port binding issues

**Solutions:**
- Increase `start_period` in docker-compose.coolify.yml
- Check application logs for startup errors
- Verify Odoo connection works
- Test health endpoint manually:
  ```bash
  curl http://localhost:8008/health
  ```

---

## Performance Optimization

### Resource Limits

**Default (docker-compose.coolify.yml):**
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

**High-Traffic Adjustment:**
```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### Horizontal Scaling

**Deploy multiple instances:**

1. Create load balancer in Coolify
2. Deploy multiple MCP instances:
   ```
   odoo-mcp-http-1 → Port 8008
   odoo-mcp-http-2 → Port 8008
   odoo-mcp-http-3 → Port 8008
   ```
3. Configure Nginx upstream in Coolify

---

## Backup & Restore

### Backup Configuration

```bash
# Export application config from Coolify
Application → Settings → Export Configuration

# Save to Git
git commit docker-compose.coolify.yml coolify.json
git push
```

### Backup Logs

```bash
# SSH to Coolify server
docker run --rm -v <project>_logs-http:/logs \
  -v $(pwd):/backup alpine \
  tar czf /backup/logs-backup-$(date +%Y%m%d).tar.gz /logs
```

### Restore

```bash
# Import in Coolify
New Resource → Import from Configuration

# Restore logs
docker run --rm -v <project>_logs-http:/logs \
  -v $(pwd):/backup alpine \
  tar xzf /backup/logs-backup.tar.gz -C /
```

---

## References

### Documentation Files

| File | Description |
|------|-------------|
| `docker-compose.coolify.yml` | Coolify-optimized Docker Compose |
| `coolify.json` | Coolify metadata configuration |
| `DOCS/COOLIFY.md` | Comprehensive deployment guide (950+ lines) |
| `COOLIFY_QUICKSTART.md` | 5-minute quick start guide |
| `DEPLOYMENT_SUMMARY.md` | This file - complete summary |

### External Resources

- **Coolify Documentation**: https://coolify.io/docs
- **Project Repository**: https://github.com/AlanOgic/mcp-odoo-adv
- **Docker Guide**: [DOCS/DOCKER.md](DOCS/DOCKER.md)
- **StreamingHTTP Guide**: [DOCS/STREAMINGHTTP_GUIDE.md](DOCS/STREAMINGHTTP_GUIDE.md)
- **Cookbook**: [COOKBOOK.md](COOKBOOK.md)

---

## Quick Command Reference

### Coolify Deployment

```bash
# Create application
Coolify → New Resource → Git Repository

# Configure
Repository: https://github.com/AlanOgic/mcp-odoo-adv
Branch: master
Compose: docker-compose.coolify.yml
Service: odoo-mcp-http

# Environment (in Coolify UI)
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password

# Deploy
Click "Deploy"
```

### Health Check

```bash
# HTTP transport
curl http://your-coolify-domain:8008/health

# SSE transport
curl http://your-coolify-domain:8009/health
```

### Test MCP Endpoint

```bash
curl -X POST http://your-coolify-domain:8008/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 1
  }'
```

### View Logs

```bash
# Coolify UI
Application → Logs

# Docker CLI (SSH to Coolify server)
docker compose logs -f odoo-mcp-http

# Application logs (inside container)
docker exec -it <container-id> tail -f /app/logs/mcp_server_*.log
```

---

## Success Criteria

Your deployment is successful when:

1. ✅ Health endpoint returns `{"status": "healthy", "odoo_connected": true}`
2. ✅ MCP endpoint responds to `tools/list` request
3. ✅ Logs show no errors
4. ✅ Coolify shows "Running" status with green indicator
5. ✅ Health checks passing (3/3)
6. ✅ SSL/TLS enabled (if configured)
7. ✅ Auto-deploy webhook working (if configured)

---

## Next Steps

After successful deployment:

1. **Configure monitoring** - Set up UptimeRobot or similar
2. **Set up alerts** - Coolify notification integrations
3. **Enable auto-deploy** - GitHub webhook configuration
4. **Test failover** - Stop container and verify restart
5. **Performance testing** - Load test with expected traffic
6. **Backup configuration** - Export and save to Git
7. **Documentation** - Document any custom configurations
8. **Security audit** - Review all settings against checklist

---

**Deployment completed successfully!** 🎉

You now have a production-ready Odoo MCP Server deployed on Coolify using Git Repository deployment, with automatic builds, health checks, persistent logs, and optional auto-deploy via webhooks.

For detailed guides:
- **Quick Start**: [COOLIFY_QUICKSTART.md](COOLIFY_QUICKSTART.md)
- **Full Guide**: [DOCS/COOLIFY.md](DOCS/COOLIFY.md)
- **Docker Details**: [DOCS/DOCKER.md](DOCS/DOCKER.md)

---

*Generated for Coolify Git Repository Deployment - Solution 1*
*Deploy with confidence. Scale with ease.* 🚀
