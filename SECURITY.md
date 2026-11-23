# Security Guide

This document provides comprehensive security guidance for deploying the Odoo MCP Server in production environments.

## Quick Start - Secure Deployment

**Minimum secure deployment:**

```bash
# 1. Generate secure Bearer token
export MCP_BEARER_TOKEN="$(openssl rand -hex 32)"

# 2. Run secure server
odoo-mcp-http-secure

# 3. Client connects with token
curl -X POST http://localhost:8008/mcp \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
```

**Production deployment:**

```bash
# 1. Use docker-compose with security hardening
docker-compose up odoo-mcp-http

# 2. Add Nginx reverse proxy (see nginx.conf.example)
# 3. Configure SSL/TLS with Let's Encrypt
# 4. Set up monitoring and logging
```

---

## Security Layers

### 1. Application-Level Authentication ✅

**FastMCP Middleware** (`src/odoo_mcp/runners/http_secure.py`)

**Features:**
- Bearer token authentication
- Constant-time token comparison (timing attack prevention)
- Request logging with IP tracking
- Works with all FastMCP transports (HTTP, SSE)

**Setup:**

```bash
# Generate strong token (64 characters recommended)
export MCP_BEARER_TOKEN="$(openssl rand -hex 32)"

# Verify token strength
echo ${#MCP_BEARER_TOKEN}  # Should be >= 64

# Run secure server
odoo-mcp-http-secure
```

**Environment Variables:**

```bash
# Required
MCP_BEARER_TOKEN="your-secure-token-here"

# Optional
MCP_HOST="0.0.0.0"          # Default: 0.0.0.0
MCP_PORT="8008"             # Default: 8008
MCP_HTTP_PATH="/mcp"        # Default: /mcp
```

**Client Usage:**

```python
# Python with FastMCP client
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.client.auth import BearerAuth

async with Client(
    transport=StreamableHttpTransport(
        "http://localhost:8008/mcp",
        auth=BearerAuth("YOUR_TOKEN_HERE")
    )
) as client:
    result = await client.ping()
```

```python
# Python with httpx
import httpx

headers = {
    "Authorization": "Bearer YOUR_TOKEN_HERE",
    "Content-Type": "application/json"
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8008/mcp",
        headers=headers,
        json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}
    )
```

**Security Properties:**

| Property | Implementation | Status |
|----------|---------------|--------|
| Token Validation | Constant-time comparison | ✅ |
| Timing Attack Prevention | `secrets.compare_digest()` | ✅ |
| Request Logging | IP + timestamp | ✅ |
| Error Messages | No token leakage | ✅ |
| Transport Support | HTTP + SSE | ✅ |

---

### 2. Network-Level Authentication 🔒

**Nginx Reverse Proxy** (`nginx.conf.example`)

**Features:**
- SSL/TLS termination
- Bearer token validation (Lua-based)
- Rate limiting
- IP whitelisting
- Security headers
- Request logging

**Setup:**

```bash
# 1. Copy example configuration
sudo cp nginx.conf.example /etc/nginx/sites-available/mcp-odoo

# 2. Update configuration
sudo nano /etc/nginx/sites-available/mcp-odoo
# - Change server_name to your domain
# - Update SSL certificate paths
# - Set your Bearer token (line 143)

# 3. Enable site
sudo ln -s /etc/nginx/sites-available/mcp-odoo /etc/nginx/sites-enabled/

# 4. Test configuration
sudo nginx -t

# 5. Reload Nginx
sudo systemctl reload nginx
```

**Key Features:**

```nginx
# Rate limiting (10 requests/second per IP)
limit_req_zone $binary_remote_addr zone=mcp_limit:10m rate=10r/s;

# Bearer token validation (Lua)
access_by_lua_block {
    local provided = ngx.var.provided_token
    local expected = ngx.var.expected_token

    # Constant-time comparison
    if #provided ~= #expected then
        ngx.exit(401)
    end

    local result = 0
    for i = 1, #provided do
        result = result | (string.byte(provided, i) ~ string.byte(expected, i))
    end

    if result ~= 0 then
        ngx.exit(401)
    end
}

# Security headers
add_header Strict-Transport-Security "max-age=31536000" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
```

**Requirements:**

```bash
# Install Nginx with Lua module
sudo apt-get install nginx-extras

# Or build from source with lua-nginx-module
# See: https://github.com/openresty/lua-nginx-module
```

---

### 3. Docker Security 🐳

**Container Hardening** (`docker-compose.yml`)

**Security Features:**

```yaml
services:
  odoo-mcp-http:
    # Read-only source code (prevents code injection)
    volumes:
      - .:/app:ro
      - ./COOKBOOK.md:/app/COOKBOOK.md:rw  # Only COOKBOOK writable
      - ./logs/http:/app/logs               # Logs writable

    # Security hardening
    security_opt:
      - no-new-privileges:true  # Prevent privilege escalation
    cap_drop:
      - ALL                     # Drop all Linux capabilities
    read_only: true             # Container filesystem read-only
    tmpfs:
      - /tmp                    # Writable temp in memory
      - /app/logs               # Writable logs in memory
```

**Security Layers:**

| Layer | Protection | Impact |
|-------|------------|--------|
| **Read-only source** | Code injection prevention | 🔴 High |
| **Selective writable mounts** | Minimized attack surface | 🟡 Medium |
| **Read-only container FS** | Malware installation prevention | 🔴 High |
| **Capability dropping** | Privilege escalation prevention | 🔴 High |
| **No new privileges** | Setuid/setgid blocking | 🟡 Medium |
| **Temporary filesystems** | Persistent malware prevention | 🟢 Low |

**Testing Security:**

There is no automated security-test script in this repo — verify by hand:

```bash
# Manual verification
docker run --rm \
  -v $(pwd):/app:ro \
  -v $(pwd)/COOKBOOK.md:/app/COOKBOOK.md:rw \
  --env-file .env \
  --entrypoint /bin/sh \
  alanogic/mcp-odoo-adv:http \
  -c "touch /app/test_write.txt 2>&1 || echo 'READ_ONLY_OK'"
```

---

## Security Best Practices

### 1. Token Management

**Generate Strong Tokens:**

```bash
# Minimum: 32 characters (64 recommended)
openssl rand -hex 32

# Strong: 64 characters
openssl rand -hex 32 | tr -d '\n'; openssl rand -hex 32 | tr -d '\n'

# Store securely in .env
echo "MCP_BEARER_TOKEN=$(openssl rand -hex 32)" >> .env
```

**Token Rotation:**

```bash
# Rotate tokens regularly (monthly recommended)
# 1. Generate new token
NEW_TOKEN=$(openssl rand -hex 32)

# 2. Update .env
sed -i "s/^MCP_BEARER_TOKEN=.*/MCP_BEARER_TOKEN=$NEW_TOKEN/" .env

# 3. Restart services
docker-compose restart

# 4. Update clients with new token
```

**Never:**
- Commit tokens to version control
- Share tokens in plain text (email, chat)
- Use weak tokens (< 32 characters)
- Reuse tokens across environments

---

### 2. Network Security

**Firewall Rules:**

```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 443/tcp     # HTTPS
sudo ufw deny 8008/tcp     # Block direct MCP access
sudo ufw enable

# Verify rules
sudo ufw status verbose
```

**IP Whitelisting (Nginx):**

```nginx
location /mcp {
    # Only allow internal network
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    allow 192.168.0.0/16;
    deny all;

    proxy_pass http://mcp_http;
}
```

**Rate Limiting:**

```nginx
# Limit to 10 requests/second per IP
limit_req_zone $binary_remote_addr zone=mcp_limit:10m rate=10r/s;

location /mcp {
    limit_req zone=mcp_limit burst=20 nodelay;
    proxy_pass http://mcp_http;
}
```

---

### 3. Monitoring & Logging

**Log Analysis:**

```bash
# Monitor authentication failures
tail -f logs/mcp_server_http_secure_*.log | grep "❌"

# Count requests per IP
awk '{print $1}' /var/log/nginx/mcp-access.log | sort | uniq -c | sort -rn

# Alert on unusual patterns
tail -f logs/mcp_server_http_secure_*.log | grep -E "(CRITICAL|ERROR|❌)"
```

**Prometheus Metrics (Future):**

```python
# Add to src/odoo_mcp/runners/http_secure.py
from prometheus_client import Counter, Histogram

auth_failures = Counter('mcp_auth_failures', 'Failed authentication attempts')
request_duration = Histogram('mcp_request_duration_seconds', 'Request duration')
```

---

### 4. SSL/TLS Configuration

**Let's Encrypt Setup:**

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d mcp.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

**Strong SSL Configuration:**

```nginx
# Use strong protocols
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;

# Enable HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

---

## Threat Model

### Threats Mitigated

| Threat | Mitigation | Layer |
|--------|------------|-------|
| **Unauthorized Access** | Bearer token authentication | Application + Network |
| **Code Injection** | Read-only source mounts | Docker |
| **Timing Attacks** | Constant-time comparison | Application |
| **DDoS** | Rate limiting | Network |
| **Man-in-the-Middle** | SSL/TLS | Network |
| **Privilege Escalation** | Capability dropping, no-new-privileges | Docker |
| **Malware Installation** | Read-only container filesystem | Docker |
| **Credential Theft** | No plaintext storage, rotation | Operational |

### Threats NOT Mitigated

| Threat | Reason | Recommended Mitigation |
|--------|--------|------------------------|
| **Odoo Server Compromise** | Out of scope | Secure Odoo instance separately |
| **Insider Threats** | Application-level | Implement audit logging, RBAC |
| **Zero-Day Vulnerabilities** | Unknown | Keep software updated, monitor CVEs |
| **Social Engineering** | Human factor | Security awareness training |

---

## Compliance

### Security Standards

**OWASP Top 10 Coverage:**

| Risk | Status | Implementation |
|------|--------|----------------|
| A01:2021 – Broken Access Control | ✅ Mitigated | Bearer token authentication |
| A02:2021 – Cryptographic Failures | ✅ Mitigated | SSL/TLS, constant-time comparison |
| A03:2021 – Injection | ✅ Mitigated | Read-only mounts, input validation |
| A04:2021 – Insecure Design | ✅ Mitigated | Defense-in-depth architecture |
| A05:2021 – Security Misconfiguration | ⚠️ Partial | Secure defaults, documentation |
| A06:2021 – Vulnerable Components | ⚠️ Partial | Dependency updates required |
| A07:2021 – Authentication Failures | ✅ Mitigated | Strong token requirements |
| A08:2021 – Data Integrity Failures | ✅ Mitigated | Read-only integrity |
| A09:2021 – Logging Failures | ✅ Mitigated | Comprehensive logging |
| A10:2021 – SSRF | ⚠️ Partial | Odoo client validation |

**PCI DSS Considerations:**

If processing payment data:
- Use SSL/TLS for all communications (✅)
- Implement strong access controls (✅)
- Maintain audit logs (✅)
- Regularly update and patch (⚠️ Manual)
- Use firewalls and network segmentation (✅)

---

## Incident Response

### Security Incident Checklist

1. **Detect:**
   ```bash
   # Check for unusual authentication failures
   grep "❌" logs/mcp_server_http_secure_*.log | tail -100

   # Check for rate limit violations
   grep "limit_req" /var/log/nginx/error.log
   ```

2. **Contain:**
   ```bash
   # Stop services immediately
   docker-compose down

   # Block suspicious IPs
   sudo ufw deny from SUSPICIOUS_IP
   ```

3. **Investigate:**
   ```bash
   # Review all logs
   cat logs/mcp_server_http_secure_*.log | grep -E "(❌|ERROR|CRITICAL)"

   # Check for unauthorized access
   cat /var/log/nginx/mcp-access.log | awk '{print $1}' | sort | uniq -c
   ```

4. **Remediate:**
   ```bash
   # Rotate all tokens
   export MCP_BEARER_TOKEN=$(openssl rand -hex 32)

   # Update .env
   sed -i "s/^MCP_BEARER_TOKEN=.*/MCP_BEARER_TOKEN=$MCP_BEARER_TOKEN/" .env

   # Restart with new credentials
   docker-compose up -d
   ```

5. **Post-Mortem:**
   - Document what happened
   - Identify root cause
   - Update security procedures
   - Notify stakeholders if required

---

## References

- **FastMCP Security**: https://github.com/jlowin/fastmcp/blob/main/docs/servers/middleware.mdx
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **Docker Security**: https://docs.docker.com/engine/security/
- **Nginx Security**: https://nginx.org/en/docs/http/ngx_http_ssl_module.html
- **Let's Encrypt**: https://letsencrypt.org/getting-started/

---

## Quick Reference

### File Locations

| File | Purpose |
|------|---------|
| `src/odoo_mcp/runners/http_secure.py` | Secure HTTP server with Bearer auth — run it via the `odoo-mcp-http-secure` console script |
| `nginx.conf.example` | Nginx reverse proxy configuration |
| `docker-compose.yml` | Docker deployment with security hardening |
| `docker-compose.prod.yml` | Production compose overlay |
| `.env` | Environment variables (DO NOT COMMIT) |

### Port Overview

| Port | Service | Security |
|------|---------|----------|
| 8008 | HTTP (insecure) | ❌ No auth |
| 8008 | HTTP (secure) | ✅ Bearer token |
| 8009 | SSE (insecure) | ❌ No auth |
| 8009 | SSE (secure) | ✅ Bearer token |
| 443 | Nginx HTTPS | ✅ SSL + auth |

### Security Checklist

- [ ] Generate strong Bearer token (64+ characters)
- [ ] Store token in `.env` file
- [ ] Add `.env` to `.gitignore`
- [ ] Use `odoo-mcp-http-secure` instead of `odoo-mcp-http`
- [ ] Configure Nginx reverse proxy
- [ ] Enable SSL/TLS with Let's Encrypt
- [ ] Set up rate limiting
- [ ] Configure IP whitelisting
- [ ] Enable Docker security hardening
- [ ] Verify container hardening manually (see **Testing Security** above)
- [ ] Set up monitoring and logging
- [ ] Document token rotation schedule
- [ ] Test incident response procedures

---

*Last Updated: 2025-01-14*
*Security is a continuous process - review and update regularly*
