# Coolify Quick Start - Git Repository Deployment

Deploy Odoo MCP Server on Coolify in 5 minutes using Git Repository.

---

## Prerequisites

- ✅ Coolify v4.0+ installed and running
- ✅ Git repository access (https://github.com/AlanOgic/mcp-odoo-adv)
- ✅ Odoo instance with API access

---

## Step 1: Create New Application in Coolify

1. **Navigate to Coolify Dashboard**
   - Log in to your Coolify instance
   - Click "**+ New Resource**"

2. **Select Application Type**
   - Choose "**Application**"
   - Select "**Git Repository**"

---

## Step 2: Configure Git Repository

**Repository Settings:**
```
Git Repository URL: https://github.com/AlanOgic/mcp-odoo-adv
Branch: master
Build Pack: Docker Compose
```

**Build Configuration:**
```
Docker Compose File Path: docker-compose.coolify.yml
Service Name: odoo-mcp-http
```

---

## Step 3: Configure Environment Variables

Click "**Environment Variables**" and add:

### Required Variables

| Variable | Value | Example |
|----------|-------|---------|
| `ODOO_URL` | Your Odoo instance URL | `https://demo.odoo.com` |
| `ODOO_DB` | Database name | `my-database` |
| `ODOO_USERNAME` | Username or email | `admin` |
| `ODOO_PASSWORD` | Password or API key | `your-password` |

**Mark `ODOO_PASSWORD` as "Secret"** to hide in UI.

### Recommended (Odoo 19+)

| Variable | Value | Example |
|----------|-------|---------|
| `ODOO_API_VERSION` | API version | `json-2` |
| `ODOO_API_KEY` | API key (replaces password) | `your-api-key` |

---

## Step 4: Configure Ports & Domains

**Port Configuration:**
```
Internal Port: 8008
Protocol: HTTP
```

**Domain (Optional):**
- Click "**Add Domain**"
- Enter: `mcp.yourdomain.com`
- Enable "**SSL**" (Let's Encrypt)

---

## Step 5: Deploy

1. Click "**Deploy**" button
2. Monitor build logs in real-time
3. Wait for "**Deployment successful**" message (2-3 minutes)

---

## Step 6: Verify Deployment

**Test Health Endpoint:**
```bash
curl http://your-coolify-domain:8008/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "odoo_connected": true
}
```

**Test MCP Endpoint:**
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

---

## Next Steps

### Enable SSE Transport (Browser Access)

**Deploy SSE as separate application:**

1. Create another application in Coolify
2. Same Git configuration
3. Change service name: `odoo-mcp-sse`
4. Change port: `8009`

### Configure Auto-Deploy

**Enable Git webhooks:**

1. Get webhook URL from Coolify:
   ```
   Application → Settings → Webhooks → Copy URL
   ```

2. Add to GitHub:
   ```
   Repository → Settings → Webhooks → Add webhook
   Payload URL: <coolify-webhook-url>
   Events: Push events
   ```

3. Push changes trigger automatic rebuild:
   ```bash
   git commit -am "Update configuration"
   git push  # Auto-deploys in Coolify
   ```

### Monitor Logs

**Real-time logs:**
```
Coolify Dashboard → Application → Logs
```

**Container logs:**
```bash
# SSH to Coolify server
docker compose logs -f odoo-mcp-http
```

---

## Common Issues

### Build Fails

**Check:**
- Dockerfile.http exists in repository
- Sufficient disk space on Coolify server
- Build logs for specific errors

### Connection Fails

**Check:**
- ODOO_URL is correct (includes `https://`)
- Network connectivity from Coolify to Odoo
- Credentials are correct
- ODOO_VERIFY_SSL setting

### Health Check Fails

**Solutions:**
- Increase start_period in docker-compose.coolify.yml
- Check application logs for errors
- Test Odoo connection manually

---

## Security Checklist

Before going to production:

- [ ] Mark ODOO_PASSWORD as "Secret"
- [ ] Use ODOO_API_KEY instead of password (Odoo 19+)
- [ ] Enable SSL/TLS with Let's Encrypt
- [ ] Configure rate limiting in Coolify
- [ ] Set up log monitoring
- [ ] Enable Coolify basic authentication (optional)
- [ ] Configure resource limits (CPU/memory)

---

## Resources

- **Full Guide**: [DOCS/COOLIFY.md](DOCS/COOLIFY.md)
- **Docker Guide**: [DOCS/DOCKER.md](DOCS/DOCKER.md)
- **StreamingHTTP Guide**: [DOCS/STREAMINGHTTP_GUIDE.md](DOCS/STREAMINGHTTP_GUIDE.md)
- **Cookbook**: [COOKBOOK.md](COOKBOOK.md)

---

## Support

- **Documentation**: https://github.com/AlanOgic/mcp-odoo-adv
- **Issues**: https://github.com/AlanOgic/mcp-odoo-adv/issues
- **Coolify Docs**: https://coolify.io/docs

---

**Deploy in 5 minutes. Scale with confidence.** 🚀
