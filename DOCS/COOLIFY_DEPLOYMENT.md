# Coolify Deployment Guide

Deploy Odoo MCP Server to Coolify with private repository support.

## Prerequisites

- Coolify instance running (self-hosted or cloud)
- Private Git repository (GitHub, GitLab, or Gitea)
- Docker images built and pushed to registry (optional)

---

## Step 1: Prepare Repository

### 1.1 Commit Changes

```bash
# Ensure all files are committed
git add .
git commit -m "Add Coolify deployment configuration"
```

### 1.2 Push to Private Repository

**GitHub:**
```bash
# Create private repo on GitHub
gh repo create mcp-odoo-adv --private --source=. --remote=origin --push

# Or manually
git remote add origin https://github.com/yourusername/mcp-odoo-adv.git
git branch -M main
git push -u origin main
```

**GitLab:**
```bash
# Create private repo on GitLab
git remote add origin https://gitlab.com/yourusername/mcp-odoo-adv.git
git branch -M main
git push -u origin main
```

**Gitea (self-hosted):**
```bash
# Create private repo on your Gitea instance
git remote add origin https://git.yourdomain.com/yourusername/mcp-odoo-adv.git
git branch -M main
git push -u origin main
```

---

## Step 2: Build and Push Docker Images (Optional)

If using custom images, build and push to your registry:

```bash
# Login to Docker Hub (or your registry)
docker login

# Build images
docker build -t yourusername/mcp-odoo-adv:http -f Dockerfile.http .
docker build -t yourusername/mcp-odoo-adv:sse -f Dockerfile.sse .

# Push images
docker push yourusername/mcp-odoo-adv:http
docker push yourusername/mcp-odoo-adv:sse

# Or use GitHub Container Registry
docker tag yourusername/mcp-odoo-adv:http ghcr.io/yourusername/mcp-odoo-adv:http
docker push ghcr.io/yourusername/mcp-odoo-adv:http
```

**Update docker-compose.coolify.yml:**
```yaml
services:
  odoo-mcp-http:
    image: yourusername/mcp-odoo-adv:http  # Change this
    # ... rest of config
```

---

## Step 3: Configure Coolify

### 3.1 Access Coolify Dashboard

1. Open Coolify UI: `https://your-coolify-instance.com`
2. Login with your credentials

### 3.2 Add Git Source

**For GitHub:**
1. Go to **Sources** → **Add New Source**
2. Select **GitHub**
3. Choose **Private Repository**
4. Generate GitHub Personal Access Token:
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Scopes needed: `repo` (all), `read:org`
   - Copy token
5. Paste token in Coolify
6. Save source

**For GitLab:**
1. Go to **Sources** → **Add New Source**
2. Select **GitLab**
3. Generate GitLab Access Token:
   - Go to GitLab → Preferences → Access Tokens
   - Scopes: `read_repository`, `read_api`
   - Copy token
4. Paste token in Coolify
5. Save source

**For Gitea:**
1. Go to **Sources** → **Add New Source**
2. Select **Gitea**
3. Enter Gitea URL: `https://git.yourdomain.com`
4. Generate Gitea Token:
   - Go to Settings → Applications → Access Tokens
   - Generate token with `repo` scope
5. Paste token in Coolify
6. Save source

### 3.3 Create New Project

1. Click **+ New Project**
2. Name: `odoo-mcp-server`
3. Description: `Odoo MCP Server - AI Assistant Integration`
4. Save project

### 3.4 Add Application

1. Inside project, click **+ New Application**
2. Select **Docker Compose**
3. Choose your Git source
4. Select repository: `mcp-odoo-adv`
5. Branch: `main`
6. Docker Compose file: `docker-compose.coolify.yml`
7. Click **Continue**

---

## Step 4: Configure Environment Variables

### 4.1 Required Variables

In Coolify application settings, add these environment variables:

| Variable | Value | Secret |
|----------|-------|--------|
| `ODOO_URL` | `https://your-instance.odoo.com` | No |
| `ODOO_DB` | `your-database` | No |
| `ODOO_USERNAME` | `your-username` | No |
| `ODOO_PASSWORD` | `your-password-or-api-key` | ✅ Yes |
| `MCP_BEARER_TOKEN` | Generate: `openssl rand -hex 32` | ✅ Yes |

### 4.2 Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ODOO_API_VERSION` | `json-2` | API version: `json-2` or `json-rpc` |
| `ODOO_TIMEOUT` | `30` | Connection timeout (seconds) |
| `ODOO_VERIFY_SSL` | `true` | Verify SSL certificates |
| `MCP_HOST` | `0.0.0.0` | Bind host |
| `MCP_PORT` | `8008` / `8009` | Service port |
| `MCP_HTTP_PATH` | `/mcp` | HTTP endpoint path |

### 4.3 Generate Secure Token

**In Coolify Terminal or locally:**
```bash
# Generate 64-character secure token
openssl rand -hex 32
# Output: e7d8f9a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0
```

Copy this token and add as `MCP_BEARER_TOKEN` in Coolify (mark as secret).

---

## Step 5: Configure Domains

### 5.1 HTTP Service Domain

1. Go to **Domains** in your application
2. Click **+ Add Domain**
3. Enter domain: `mcp.yourdomain.com`
4. Port: `8008`
5. Enable **SSL/TLS** (Let's Encrypt)
6. Save

### 5.2 SSE Service Domain

1. Click **+ Add Domain**
2. Enter domain: `sse.mcp.yourdomain.com`
3. Port: `8009`
4. Enable **SSL/TLS**
5. Save

### 5.3 DNS Configuration

Add DNS records pointing to your Coolify server:

```
Type  Name                Value                    TTL
A     mcp                 YOUR_COOLIFY_IP         300
A     sse.mcp             YOUR_COOLIFY_IP         300
```

Wait for DNS propagation (1-5 minutes).

---

## Step 6: Configure Volumes (Persistent Storage)

### 6.1 Application Logs

1. Go to **Volumes** → **+ Add Volume**
2. Name: `http-logs`
3. Mount path: `/app/logs`
4. Type: **Named Volume**
5. Save

Repeat for `sse-logs`.

### 6.2 COOKBOOK.md (Self-Learning)

1. **+ Add Volume**
2. Name: `cookbook`
3. Mount path: `/app/COOKBOOK.md`
4. Type: **Named Volume**
5. Save

This preserves learned patterns across deployments.

---

## Step 7: Deploy Application

### 7.1 Initial Deployment

1. Click **Deploy** button
2. Coolify will:
   - Clone private repository
   - Pull Docker images
   - Create volumes
   - Start containers
   - Configure networking
   - Generate SSL certificates

### 7.2 Monitor Deployment

Watch logs in Coolify UI:
```
Pulling images...
Creating network...
Creating volumes...
Starting odoo-mcp-http...
Starting odoo-mcp-sse...
Waiting for health checks...
✅ Deployment successful!
```

### 7.3 Check Health

```bash
# HTTP service
curl -H "Authorization: Bearer YOUR_TOKEN" https://mcp.yourdomain.com/health

# SSE service
curl -H "Authorization: Bearer YOUR_TOKEN" https://sse.mcp.yourdomain.com/health
```

Expected response: `OK`

---

## Step 8: Test MCP Server

### 8.1 List Tools

```bash
curl -X POST https://mcp.yourdomain.com/mcp \
  -H "Authorization: Bearer YOUR_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 1
  }'
```

### 8.2 Execute Odoo Method

```bash
curl -X POST https://mcp.yourdomain.com/mcp \
  -H "Authorization: Bearer YOUR_BEARER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "execute_method",
      "arguments": {
        "model": "res.partner",
        "method": "search_read",
        "kwargs_json": "{\"limit\": 5, \"fields\": [\"name\", \"email\"]}"
      }
    },
    "id": 2
  }'
```

### 8.3 Python Client

```python
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.client.auth import BearerAuth

async with Client(
    transport=StreamableHttpTransport(
        "https://mcp.yourdomain.com/mcp",
        auth=BearerAuth("YOUR_BEARER_TOKEN")
    )
) as client:
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {len(tools)}")

    # Call execute_method
    result = await client.call_tool(
        "execute_method",
        {
            "model": "res.partner",
            "method": "search_read",
            "kwargs_json": '{"limit": 5, "fields": ["name", "email"]}'
        }
    )
    print(f"Result: {result.data}")
```

---

## Step 9: Monitoring & Maintenance

### 9.1 View Logs

**In Coolify UI:**
1. Go to your application
2. Click **Logs** tab
3. Select service: `odoo-mcp-http` or `odoo-mcp-sse`
4. Real-time log streaming

**Via SSH to Coolify server:**
```bash
# HTTP service logs
docker logs odoo-mcp-http -f

# SSE service logs
docker logs odoo-mcp-sse -f

# Persistent logs (if mounted)
docker exec odoo-mcp-http cat /app/logs/mcp_server_http_*.log
```

### 9.2 Health Checks

Coolify automatically monitors health checks every 30s:
- HTTP: `http://localhost:8008/health`
- SSE: `http://localhost:8009/health`

If health check fails 3 times, Coolify will restart the container.

### 9.3 Resource Usage

**In Coolify:**
- Go to **Metrics** tab
- View CPU, Memory, Network usage
- Set up alerts for high resource usage

**Resource Limits:**
```yaml
# In docker-compose.coolify.yml
deploy:
  resources:
    limits:
      cpus: '1'          # Max 1 CPU core
      memory: 512M       # Max 512MB RAM
    reservations:
      cpus: '0.25'       # Reserve 25% CPU
      memory: 128M       # Reserve 128MB RAM
```

### 9.4 Backups

**COOKBOOK.md Backups:**
```bash
# SSH to Coolify server
ssh user@coolify-server

# Find volume location
docker volume inspect mcp-odoo-adv_cookbook
# Output: "Mountpoint": "/var/lib/docker/volumes/mcp-odoo-adv_cookbook/_data"

# Backup COOKBOOK
sudo cp /var/lib/docker/volumes/mcp-odoo-adv_cookbook/_data/COOKBOOK.md \
  ~/backups/cookbook_$(date +%Y%m%d_%H%M%S).md

# Automated daily backup (cron)
echo "0 2 * * * sudo cp /var/lib/docker/volumes/mcp-odoo-adv_cookbook/_data/COOKBOOK.md ~/backups/cookbook_\$(date +\%Y\%m\%d).md" | crontab -
```

---

## Step 10: Continuous Deployment

### 10.1 Auto-Deploy on Push

**Enable in Coolify:**
1. Go to application settings
2. Enable **Auto Deploy**
3. Select **Branch**: `main`
4. Save

Now every push to `main` branch triggers automatic deployment:
```bash
git add .
git commit -m "Update feature"
git push origin main
# Coolify automatically deploys
```

### 10.2 Webhooks

Coolify provides webhook URL for manual triggers:

```bash
# Get webhook URL from Coolify UI
# Example: https://coolify.yourdomain.com/webhooks/abc123def456

# Trigger deployment manually
curl -X POST https://coolify.yourdomain.com/webhooks/abc123def456
```

**GitHub Actions Integration:**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Coolify

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Coolify Deployment
        run: |
          curl -X POST ${{ secrets.COOLIFY_WEBHOOK_URL }}
```

### 10.3 Rollback

**In Coolify UI:**
1. Go to **Deployments** tab
2. View deployment history
3. Click **Rollback** on previous successful deployment

**Via CLI:**
```bash
# SSH to Coolify server
coolify deployment rollback --app odoo-mcp-server --version previous
```

---

## Troubleshooting

### Issue: Health Check Failing

**Symptoms:**
- Container keeps restarting
- Logs show: "Health check failed"

**Solution:**
```bash
# Check if Bearer token is set
docker exec odoo-mcp-http env | grep MCP_BEARER_TOKEN

# Test health endpoint manually
docker exec odoo-mcp-http curl -f http://localhost:8008/health \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check if secure server is running
docker exec odoo-mcp-http ps aux | grep python
```

**Fix:**
Ensure `MCP_BEARER_TOKEN` is set in Coolify environment variables.

---

### Issue: Cannot Connect to Odoo

**Symptoms:**
- Logs show: "Connection refused" or "Timeout"

**Solution:**
```bash
# Check Odoo connectivity from container
docker exec odoo-mcp-http curl -I https://your-instance.odoo.com

# Check environment variables
docker exec odoo-mcp-http env | grep ODOO_

# Test Odoo authentication
docker exec odoo-mcp-http python -c "
from src.odoo_mcp.odoo_client import get_odoo_client
client = get_odoo_client()
print('Connected:', client is not None)
"
```

**Fix:**
- Verify `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD` in Coolify
- Check if Odoo instance allows external connections
- Verify firewall rules on Coolify server

---

### Issue: SSL Certificate Errors

**Symptoms:**
- `ERR_SSL_PROTOCOL_ERROR`
- "SSL certificate problem"

**Solution:**
```bash
# Check SSL certificate status
curl -vI https://mcp.yourdomain.com

# Verify Let's Encrypt certificate
openssl s_client -connect mcp.yourdomain.com:443 -servername mcp.yourdomain.com

# Check Coolify certificate renewal
docker logs coolify-proxy | grep certificate
```

**Fix:**
1. In Coolify, go to domain settings
2. Click **Renew Certificate**
3. Wait for Let's Encrypt validation (2-5 minutes)

---

### Issue: Volume Data Not Persisting

**Symptoms:**
- COOKBOOK.md resets after deployment
- Logs disappear

**Solution:**
```bash
# Check volume mounts
docker inspect odoo-mcp-http | grep Mounts -A 20

# Verify volume exists
docker volume ls | grep cookbook

# Check volume data
docker run --rm -v mcp-odoo-adv_cookbook:/data alpine ls -la /data
```

**Fix:**
Ensure volumes are defined in `docker-compose.coolify.yml`:
```yaml
volumes:
  - cookbook:/app/COOKBOOK.md
```

---

## Security Considerations

### 1. Secrets Management

✅ **Do:**
- Store all secrets in Coolify environment variables
- Mark sensitive variables as "Secret" in Coolify UI
- Use 64+ character Bearer tokens
- Rotate tokens monthly

❌ **Don't:**
- Commit secrets to Git
- Share tokens via email/chat
- Use weak tokens (< 32 characters)

### 2. Network Security

**Coolify automatically provides:**
- ✅ SSL/TLS termination (Let's Encrypt)
- ✅ HTTP → HTTPS redirect
- ✅ Isolated Docker network

**Additional hardening:**
```bash
# SSH to Coolify server and configure firewall
sudo ufw default deny incoming
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable

# Verify
sudo ufw status verbose
```

### 3. Rate Limiting

Add Nginx rate limiting in Coolify:

1. Go to application → **Advanced** → **Custom Nginx Config**
2. Add:
```nginx
limit_req_zone $binary_remote_addr zone=mcp_limit:10m rate=10r/s;

location /mcp {
    limit_req zone=mcp_limit burst=20 nodelay;
    proxy_pass http://odoo-mcp-http:8008;
}
```

---

## Performance Optimization

### 1. Resource Scaling

**Horizontal Scaling:**
```yaml
# In docker-compose.coolify.yml
services:
  odoo-mcp-http:
    deploy:
      replicas: 3  # Run 3 instances
      resources:
        limits:
          cpus: '2'
          memory: 1G
```

**Vertical Scaling:**
Adjust resource limits based on usage:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'        # Increase CPU
      memory: 2G       # Increase RAM
```

### 2. Caching

Enable response caching in Nginx:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=mcp_cache:10m max_size=100m;

location /mcp {
    proxy_cache mcp_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
}
```

---

## Cost Estimation

**Coolify Server Requirements:**

| Users | CPU | RAM | Disk | Cost/Month |
|-------|-----|-----|------|------------|
| 1-10 | 1 core | 2GB | 20GB | $5-10 (DigitalOcean, Hetzner) |
| 10-50 | 2 cores | 4GB | 40GB | $12-20 |
| 50-200 | 4 cores | 8GB | 80GB | $24-40 |

**Additional Costs:**
- Domain name: $10-15/year
- SSL certificate: Free (Let's Encrypt)
- Backups: $1-5/month (object storage)

---

## References

- **Coolify Docs**: https://coolify.io/docs
- **Docker Compose**: https://docs.docker.com/compose/
- **Let's Encrypt**: https://letsencrypt.org/
- **MCP Server Docs**: See `README.md`, `COOKBOOK.md`, `SECURITY.md`

---

## Quick Command Reference

```bash
# Deployment
git push origin main              # Auto-deploy (if enabled)
curl -X POST WEBHOOK_URL          # Manual deployment

# Logs
docker logs odoo-mcp-http -f     # Real-time HTTP logs
docker logs odoo-mcp-sse -f      # Real-time SSE logs

# Health check
curl https://mcp.yourdomain.com/health -H "Authorization: Bearer TOKEN"

# Restart services
docker restart odoo-mcp-http
docker restart odoo-mcp-sse

# Backup COOKBOOK
docker cp odoo-mcp-http:/app/COOKBOOK.md ./backup/cookbook_$(date +%Y%m%d).md

# Update environment variables
# (Do this in Coolify UI, then restart)
docker restart odoo-mcp-http

# View resource usage
docker stats odoo-mcp-http odoo-mcp-sse
```

---

*Last Updated: 2025-01-14*
*Coolify Version: 4.0+*
