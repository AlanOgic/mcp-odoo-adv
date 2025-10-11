# Coolify Deployment Guide

Complete guide for deploying Odoo MCP Server on Coolify using Git Repository deployment.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Deployment Methods](#deployment-methods)
- [Configuration](#configuration)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Security Best Practices](#security-best-practices)
- [Advanced Configuration](#advanced-configuration)

---

## Quick Start

### 5-Minute Deployment

1. **Create New Resource in Coolify**
   - Navigate to your Coolify dashboard
   - Click "New Resource"
   - Select "Application"
   - Choose "Git Repository"

2. **Configure Git Repository**
   ```
   Repository URL: https://github.com/AlanOgic/mcp-odoo-adv
   Branch: master
   Build Pack: Docker Compose
   ```

3. **Set Compose File**
   ```
   Docker Compose File: docker-compose.coolify.yml
   Service: odoo-mcp-http
   ```

4. **Configure Environment Variables**

   **Required:**
   ```bash
   ODOO_URL=https://your-instance.odoo.com
   ODOO_DB=your-database
   ODOO_USERNAME=your-username
   ODOO_PASSWORD=your-password
   ```

   **Recommended (Odoo 19+):**
   ```bash
   ODOO_API_VERSION=json-2
   ODOO_API_KEY=your-api-key  # Replaces ODOO_PASSWORD
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Access at: `http://your-coolify-domain:8008`

---

## Prerequisites

### Coolify Requirements

- **Coolify v4.0+** (latest stable version recommended)
- **Docker Engine 20.10+** on Coolify server
- **Minimum 512MB RAM** per service
- **1GB disk space** for images and logs

### Odoo Requirements

- **Odoo 14+** instance (Odoo 19+ recommended)
- **API access** credentials (username/password or API key)
- **Network access** from Coolify server to Odoo instance

### Git Repository Access

- Public repository: No authentication needed
- Private repository: Configure SSH key or access token in Coolify

---

## Deployment Methods

### Method 1: Git Repository (Recommended)

**Advantages:**
- ✅ Automatic builds from source
- ✅ Full control over configuration
- ✅ Easy updates via Git commits
- ✅ No Docker Hub dependency

**Disadvantages:**
- ⚠️ Longer initial build time (2-3 minutes)
- ⚠️ Requires Git repository access

**Step-by-Step:**

1. **Create Application**
   ```
   Coolify Dashboard → New Resource → Application → Git Repository
   ```

2. **Repository Configuration**
   ```yaml
   Repository: https://github.com/AlanOgic/mcp-odoo-adv
   Branch: master
   Build Pack: Docker Compose
   Compose File: docker-compose.coolify.yml
   Service: odoo-mcp-http
   ```

3. **Port Configuration**
   - Coolify will auto-detect port 8008 from docker-compose.coolify.yml
   - Enable "Public Port" to expose externally
   - Configure domain/subdomain if desired

4. **Environment Variables** (see [Configuration](#configuration))

5. **Build Settings**
   - Build Command: (leave empty - uses Dockerfile.http)
   - Post-deployment Command: (optional - see [Advanced](#advanced-configuration))

6. **Deploy**
   - Click "Deploy" button
   - Monitor build logs in real-time
   - Wait for "Deployment successful" message

### Method 2: SSE Transport (Browser Access)

Deploy both HTTP and SSE transports for different use cases:

1. **Deploy HTTP transport** (following Method 1)

2. **Enable SSE service**

   In Coolify, edit the application:
   ```yaml
   # Enable SSE profile in docker-compose
   Environment Variables:
     COMPOSE_PROFILES=sse
   ```

3. **Or deploy SSE as separate application**
   ```yaml
   Same Git configuration
   Service: odoo-mcp-sse
   Port: 8009
   ```

---

## Configuration

### Environment Variables

#### Required Variables

```bash
# Odoo Connection
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password
```

**Set in Coolify:**
```
Application Settings → Environment Variables → Add Variable
```

Mark `ODOO_PASSWORD` as "Secret" to hide value in UI.

#### Recommended Variables (Odoo 19+)

```bash
# Use JSON-2 API with API key (more secure)
ODOO_API_VERSION=json-2
ODOO_API_KEY=your-api-key

# Remove ODOO_PASSWORD when using API key
```

#### Optional Variables

```bash
# Connection Settings
ODOO_TIMEOUT=30              # Connection timeout (seconds)
ODOO_VERIFY_SSL=1            # SSL verification (1=enabled, 0=disabled)

# Proxy Settings
HTTP_PROXY=http://proxy:8080
HTTPS_PROXY=http://proxy:8080

# Server Settings
DEBUG=0                      # Debug logging (1=enabled)
HTTP_PORT=8008              # HTTP server port
SSE_PORT=8009               # SSE server port

# Build Settings
PYTHON_VERSION=3.12         # Python version (3.10-3.14)
```

### Port Configuration

**HTTP Transport (default):**
```
Internal Port: 8008
External Port: Auto-assigned by Coolify (or custom)
Protocol: HTTP
```

**SSE Transport:**
```
Internal Port: 8009
External Port: Auto-assigned by Coolify (or custom)
Protocol: HTTP
```

**Coolify Port Mapping:**
- Navigate to "Domains & Ports"
- Add custom domain or use Coolify proxy
- Enable SSL/TLS via Let's Encrypt (recommended)

### Volume Configuration

Persistent logs are automatically configured in `docker-compose.coolify.yml`:

```yaml
volumes:
  logs-http:
    driver: local
  logs-sse:
    driver: local
```

**Access logs in Coolify:**
```
Application → Logs → Container Logs
```

**Or via Docker volume:**
```bash
# SSH into Coolify server
docker volume inspect mcp-odoo-adv_logs-http
```

---

## Monitoring & Troubleshooting

### Health Checks

Health checks are pre-configured in `docker-compose.coolify.yml`:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8008/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**View health status:**
```
Coolify Dashboard → Application → Status
```

### Log Monitoring

**Real-time logs in Coolify:**
```
Application → Logs → Show Logs
```

**Container logs via CLI:**
```bash
# SSH to Coolify server
docker compose -f /path/to/deployment/docker-compose.yml logs -f odoo-mcp-http
```

**Application logs (inside container):**
```bash
docker exec -it <container-id> tail -f /app/logs/mcp_server_*.log
```

### Common Issues

#### 1. Build Failures

**Error:** `Failed to build image`

**Solutions:**
- Check Dockerfile.http exists in repository
- Verify Python version in build args (3.10-3.14)
- Check build logs for specific errors
- Ensure sufficient disk space on Coolify server

```bash
# Check available space
df -h
```

#### 2. Connection Errors

**Error:** `Cannot connect to Odoo instance`

**Solutions:**
- Verify ODOO_URL is correct (must include https://)
- Check network connectivity from Coolify server:
  ```bash
  curl -I https://your-instance.odoo.com
  ```
- Verify credentials (username/password or API key)
- Check SSL verification setting (ODOO_VERIFY_SSL)

#### 3. Authentication Failures

**Error:** `Authentication failed`

**Solutions:**
- Verify ODOO_USERNAME and ODOO_PASSWORD are correct
- For Odoo 19+: Use ODOO_API_KEY instead of password
- Check ODOO_DB matches your database name
- Verify API access is enabled in Odoo

#### 4. Port Conflicts

**Error:** `Port 8008 already in use`

**Solutions:**
- Change HTTP_PORT environment variable
- Update docker-compose.coolify.yml port mapping
- Check for conflicting services in Coolify

#### 5. Health Check Failures

**Error:** `Health check failed`

**Solutions:**
- Increase start_period in docker-compose.coolify.yml
- Check application logs for startup errors
- Verify Odoo connection is working
- Test health endpoint manually:
  ```bash
  curl http://localhost:8008/health
  ```

### Debugging Steps

1. **Check deployment logs**
   ```
   Coolify → Application → Logs → Build Logs
   ```

2. **Check container logs**
   ```
   Coolify → Application → Logs → Container Logs
   ```

3. **Test health endpoint**
   ```bash
   # From Coolify server
   curl http://localhost:8008/health

   # Expected response:
   {"status": "healthy", "odoo_connected": true}
   ```

4. **Test MCP endpoint**
   ```bash
   curl -X POST http://localhost:8008/mcp \
     -H "Content-Type: application/json" \
     -d '{
       "jsonrpc": "2.0",
       "method": "tools/list",
       "params": {},
       "id": 1
     }'
   ```

5. **Check Odoo connectivity**
   ```bash
   # SSH to Coolify server
   docker exec -it <container-id> python3 -c "
   import os
   from odoo_mcp.odoo_client import get_odoo_client
   client = get_odoo_client()
   print('Connected:', client.uid is not None)
   "
   ```

---

## Security Best Practices

### 1. Use Environment Variables for Secrets

**Never** commit credentials to Git:

```bash
# ✅ Good - Use Coolify environment variables
ODOO_PASSWORD=secret123

# ❌ Bad - Hardcoded in docker-compose.yml
ODOO_PASSWORD=secret123  # Don't do this!
```

**In Coolify:**
- Mark sensitive variables as "Secret"
- Use "Build Time" secrets for build args
- Use "Runtime" secrets for application config

### 2. Enable SSL/TLS

**Configure in Coolify:**
```
Application → Domains → Add Domain → Enable SSL
```

Coolify auto-provisions Let's Encrypt certificates.

**For custom SSL:**
```
Application → Domains → Custom Certificate
```

### 3. Restrict Access

**Option 1: Coolify Built-in Auth**
```
Application → Security → Enable Basic Authentication
```

**Option 2: Network Isolation**
```
Application → Network → Private Network Only
```

**Option 3: Reverse Proxy with Auth**
```nginx
# Nginx configuration in Coolify
location /mcp {
    auth_basic "MCP Server";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://odoo-mcp-http:8008;
}
```

### 4. Use API Keys (Odoo 19+)

```bash
# ✅ Preferred - API key authentication
ODOO_API_VERSION=json-2
ODOO_API_KEY=your-api-key

# ❌ Less secure - Password authentication
ODOO_API_VERSION=json-rpc
ODOO_PASSWORD=your-password
```

### 5. Enable Rate Limiting

**Configure in Coolify proxy:**
```
Application → Advanced → Rate Limiting
Requests per minute: 100
Burst: 20
```

### 6. Regular Updates

**Keep application updated:**
```bash
# In Git repository
git pull origin master

# Trigger rebuild in Coolify
Coolify → Application → Redeploy
```

**Update dependencies:**
```bash
# Update pyproject.toml
pip install -U fastmcp requests

# Commit and push
git commit -am "Update dependencies"
git push
```

### 7. Monitor Logs

**Enable log retention:**
```yaml
# In docker-compose.coolify.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "5"  # Increase retention
```

**Set up log monitoring:**
```
Coolify → Application → Logs → Enable Log Alerts
```

---

## Advanced Configuration

### Multi-Environment Deployment

Deploy separate instances for dev/staging/prod:

**Development Environment:**
```yaml
# Coolify Application: "odoo-mcp-dev"
Environment:
  ODOO_URL: https://dev.odoo.example.com
  ODOO_DB: dev-database
  DEBUG: 1
```

**Staging Environment:**
```yaml
# Coolify Application: "odoo-mcp-staging"
Environment:
  ODOO_URL: https://staging.odoo.example.com
  ODOO_DB: staging-database
  DEBUG: 0
```

**Production Environment:**
```yaml
# Coolify Application: "odoo-mcp-prod"
Environment:
  ODOO_URL: https://odoo.example.com
  ODOO_DB: production-database
  DEBUG: 0
  ODOO_API_VERSION: json-2
  ODOO_API_KEY: ${SECRET_API_KEY}
```

### Custom Build Configuration

**Use custom Dockerfile:**

1. Create `Dockerfile.custom` in repository:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
# Custom build steps
COPY . .
RUN pip install -e .
ENTRYPOINT ["python", "run_server_http.py"]
```

2. Update Coolify build settings:
```
Build Pack: Dockerfile
Dockerfile: Dockerfile.custom
```

### Resource Limits

**Configure in docker-compose.coolify.yml:**

```yaml
services:
  odoo-mcp-http:
    deploy:
      resources:
        limits:
          cpus: '2.0'        # Increase CPU limit
          memory: 1G          # Increase memory limit
        reservations:
          cpus: '0.5'
          memory: 512M
```

**Or in Coolify UI:**
```
Application → Resources → Container Resources
```

### Horizontal Scaling

**Deploy multiple instances:**

1. **Create load balancer application** in Coolify
2. **Deploy multiple MCP instances:**
   ```
   odoo-mcp-http-1 → Port 8008
   odoo-mcp-http-2 → Port 8008
   odoo-mcp-http-3 → Port 8008
   ```

3. **Configure load balancer:**
   ```nginx
   upstream mcp_backend {
       least_conn;
       server odoo-mcp-http-1:8008;
       server odoo-mcp-http-2:8008;
       server odoo-mcp-http-3:8008;
   }

   server {
       listen 80;
       location /mcp {
           proxy_pass http://mcp_backend;
       }
   }
   ```

### Custom Domain Configuration

**Add custom domain:**
```
Coolify → Application → Domains → Add Domain
Domain: mcp.yourdomain.com
Enable SSL: Yes (Let's Encrypt)
```

**Configure DNS:**
```
Type: A Record
Name: mcp
Value: <coolify-server-ip>
TTL: 300
```

### Webhook Auto-Deploy

**Enable Git webhooks for auto-deployment:**

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

3. **Auto-deploy on Git push:**
   ```bash
   git commit -am "Update configuration"
   git push  # Triggers automatic rebuild in Coolify
   ```

### Backup & Restore

**Backup configuration:**
```bash
# Export Coolify application config
Coolify → Application → Settings → Export Configuration

# Save docker-compose.coolify.yml
git commit docker-compose.coolify.yml
```

**Backup logs:**
```bash
# SSH to Coolify server
docker run --rm -v mcp-odoo-adv_logs-http:/logs \
  -v $(pwd):/backup alpine \
  tar czf /backup/logs-backup.tar.gz /logs
```

**Restore from backup:**
```bash
# Import configuration in Coolify
Coolify → New Resource → Import from Configuration

# Restore logs
docker run --rm -v mcp-odoo-adv_logs-http:/logs \
  -v $(pwd):/backup alpine \
  tar xzf /backup/logs-backup.tar.gz -C /
```

---

## Production Checklist

Before deploying to production:

- [ ] Use ODOO_API_KEY instead of ODOO_PASSWORD (Odoo 19+)
- [ ] Enable SSL/TLS with Let's Encrypt
- [ ] Set DEBUG=0
- [ ] Configure rate limiting
- [ ] Set up log monitoring and alerts
- [ ] Configure resource limits (CPU/memory)
- [ ] Enable health checks
- [ ] Restrict network access (private network or auth)
- [ ] Test failover and recovery procedures
- [ ] Document deployment process
- [ ] Set up automated backups
- [ ] Configure monitoring/alerting (e.g., UptimeRobot)
- [ ] Test with production-like load
- [ ] Review security settings
- [ ] Configure log rotation
- [ ] Set up Git webhooks for auto-deploy

---

## References

- **Coolify Documentation**: https://coolify.io/docs
- **Odoo MCP Server**: https://github.com/AlanOgic/mcp-odoo-adv
- **Docker Guide**: [DOCKER.md](DOCKER.md)
- **StreamingHTTP Guide**: [STREAMINGHTTP_GUIDE.md](STREAMINGHTTP_GUIDE.md)
- **Cookbook**: [COOKBOOK.md](../COOKBOOK.md)

---

**Deploy with confidence.** 🚀
