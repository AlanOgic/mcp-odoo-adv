# Security Guide

**Odoo MCP Server Advanced - Production Security Best Practices**

## Overview

The MCP server provides **no built-in authentication**. Security must be implemented at the infrastructure level using a reverse proxy (Nginx, Caddy, Traefik).

### Threat Model

| Transport | Attack Surface | Risk Level |
|-----------|---------------|------------|
| **STDIO** | None (local process) | ✅ Low |
| **SSE** | Network exposed | ⚠️ High |
| **Streamable HTTP** | Network exposed | ⚠️ High |

**Critical**: SSE and HTTP transports expose your Odoo instance to network attacks without proper security.

---

## Quick Start: Security Checklist

Before deploying to production:

- [ ] **SSL/TLS configured** (Let's Encrypt or commercial certificate)
- [ ] **Authentication enabled** (API Key, Basic Auth, or mTLS)
- [ ] **Rate limiting active** (prevent DoS attacks)
- [ ] **IP whitelisting configured** (restrict to known networks)
- [ ] **Logs monitored** (security events and anomalies)
- [ ] **Secrets secured** (environment variables, not hardcoded)
- [ ] **Firewall configured** (block direct access to ports 8008/8009)
- [ ] **Regular updates** (OS, Nginx, MCP server)

---

## Authentication Methods

### Comparison

| Method | Security | Complexity | Use Case |
|--------|----------|-----------|----------|
| **API Key** | Medium | Low | Simple server-to-server |
| **Basic Auth** | Medium | Low | Development/testing |
| **mTLS** | High | High | Enterprise, maximum security |
| **Combined** | Very High | Medium | Production recommended |

### 1. API Key Authentication

**Best for**: Server-to-server integrations, API clients

**Security**: Medium (requires HTTPS to prevent key exposure)

**Setup**: See [TRANSPORTS.md - Option 1](TRANSPORTS.md#option-1-api-key-authentication)

**Pros**:
- Simple to implement
- Easy to rotate keys
- No user management

**Cons**:
- Single point of failure if key is compromised
- No per-user permissions

**Client Example**:
```bash
curl -X POST https://mcp.yourdomain.com/mcp \
  -H "X-API-Key: your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
```

### 2. Basic Authentication

**Best for**: Development, internal tools, quick prototypes

**Security**: Medium (credentials sent with each request)

**Setup**: See [TRANSPORTS.md - Option 2](TRANSPORTS.md#option-2-basic-authentication)

**Pros**:
- Built into HTTP standard
- Supported by all clients
- Per-user credentials

**Cons**:
- Base64 encoding (not encryption)
- Credentials in every request
- No advanced features (2FA, OAuth)

**Client Example**:
```bash
curl -X POST https://mcp.yourdomain.com/mcp \
  -u username:password \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
```

### 3. Mutual TLS (mTLS)

**Best for**: Enterprise deployments, maximum security requirements

**Security**: High (certificate-based, cryptographic proof)

**Setup**: See [TRANSPORTS.md - Option 3](TRANSPORTS.md#option-3-mutual-tls-mtls)

**Pros**:
- Strongest authentication
- Client certificate validation
- No password transmission

**Cons**:
- Complex certificate management
- Certificate distribution challenges
- Renewal overhead

**Client Example**:
```bash
curl -X POST https://mcp.yourdomain.com/mcp \
  --cert client.crt \
  --key client.key \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
```

### 4. Combined Security (Recommended)

**Best for**: Production deployments

Layers multiple security controls:
- SSL/TLS encryption
- API key authentication
- Rate limiting
- IP whitelisting
- Security headers

**Setup**: See [TRANSPORTS.md - Option 4](TRANSPORTS.md#option-4-combined-security-recommended)

---

## SSL/TLS Configuration

### Let's Encrypt (Free)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d mcp.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Commercial Certificate

```bash
# Generate CSR
openssl req -new -newkey rsa:4096 -nodes \
  -keyout mcp.yourdomain.com.key \
  -out mcp.yourdomain.com.csr

# Submit CSR to certificate authority
# Install received certificate in Nginx
```

### SSL Best Practices

```nginx
# Strong SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers on;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
```

---

## Rate Limiting

Prevent DoS attacks and abuse.

### Basic Rate Limiting

```nginx
# 10 requests per second per IP
limit_req_zone $binary_remote_addr zone=mcp:10m rate=10r/s;

location /mcp {
    limit_req zone=mcp burst=20 nodelay;
    # ... proxy settings
}
```

### Advanced Rate Limiting

```nginx
# Different limits for different endpoints
limit_req_zone $binary_remote_addr zone=mcp_tools:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=mcp_resources:10m rate=20r/s;

# Apply based on request path
location ~* /mcp/(tools|execute) {
    limit_req zone=mcp_tools burst=20 nodelay;
}

location ~* /mcp/resources {
    limit_req zone=mcp_resources burst=50 nodelay;
}
```

### Rate Limit Response

```nginx
# Custom error page for rate limiting
error_page 429 = @rate_limit;

location @rate_limit {
    return 429 '{"error": "Rate limit exceeded. Please slow down."}';
    add_header Content-Type application/json always;
}
```

---

## IP Whitelisting

### Private Networks Only

```nginx
location /mcp {
    # Allow RFC 1918 private networks
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    allow 192.168.0.0/16;
    deny all;
}
```

### Specific IPs/Networks

```nginx
location /mcp {
    # Corporate office
    allow 203.0.113.0/24;

    # Remote office VPN
    allow 198.51.100.50;

    # Cloud provider IPs
    allow 192.0.2.0/24;

    deny all;
}
```

### Dynamic IP Whitelist

```nginx
# Load IPs from file
geo $whitelist {
    default 0;
    include /etc/nginx/whitelist.conf;
}

location /mcp {
    if ($whitelist = 0) {
        return 403 '{"error": "Access denied - IP not whitelisted"}';
    }
    # ... proxy settings
}
```

File `/etc/nginx/whitelist.conf`:
```
203.0.113.0/24 1;
198.51.100.50 1;
192.0.2.0/24 1;
```

---

## Security Headers

### Essential Headers

```nginx
# HSTS - Force HTTPS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# Prevent MIME sniffing
add_header X-Content-Type-Options "nosniff" always;

# Prevent clickjacking
add_header X-Frame-Options "DENY" always;

# XSS protection
add_header X-XSS-Protection "1; mode=block" always;

# CSP (adjust for your needs)
add_header Content-Security-Policy "default-src 'self'" always;

# Referrer policy
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

### CORS Configuration

For browser-based clients:

```nginx
# Allow specific origin
add_header Access-Control-Allow-Origin "https://your-app.com" always;
add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
add_header Access-Control-Allow-Headers "Content-Type, X-API-Key" always;
add_header Access-Control-Max-Age "3600" always;

# Handle preflight
if ($request_method = OPTIONS) {
    return 204;
}
```

---

## Logging and Monitoring

### Nginx Access Logs

```nginx
# Detailed logging format
log_format mcp_detailed '$remote_addr - $remote_user [$time_local] '
                        '"$request" $status $body_bytes_sent '
                        '"$http_referer" "$http_user_agent" '
                        '"$http_x_api_key" $request_time';

access_log /var/log/nginx/mcp_access.log mcp_detailed;
error_log /var/log/nginx/mcp_error.log warn;
```

### Failed Authentication Monitoring

```bash
# Monitor failed API key attempts
tail -f /var/log/nginx/mcp_access.log | grep "401"

# Count failed attempts per IP
awk '$9 == 401 {print $1}' /var/log/nginx/mcp_access.log | sort | uniq -c | sort -rn
```

### Log Rotation

```bash
# /etc/logrotate.d/mcp-nginx
/var/log/nginx/mcp_*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

### Alerting

**Fail2ban** - Auto-ban abusive IPs:

```ini
# /etc/fail2ban/filter.d/nginx-mcp.conf
[Definition]
failregex = ^<HOST> .* "(GET|POST) /mcp .* 401
ignoreregex =

# /etc/fail2ban/jail.local
[nginx-mcp]
enabled = true
port = http,https
filter = nginx-mcp
logpath = /var/log/nginx/mcp_access.log
maxretry = 5
bantime = 3600
```

---

## Secrets Management

### Environment Variables (Recommended)

```bash
# /etc/systemd/system/mcp-odoo-http.service
[Service]
EnvironmentFile=/etc/mcp-odoo/secrets.env
```

File `/etc/mcp-odoo/secrets.env`:
```bash
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=api_user
ODOO_PASSWORD=secure_password_here

# Restrict permissions
# chmod 600 /etc/mcp-odoo/secrets.env
# chown mcp:mcp /etc/mcp-odoo/secrets.env
```

### Vault Integration (Advanced)

```bash
# Fetch secrets from HashiCorp Vault
export VAULT_ADDR='https://vault.company.com'
export VAULT_TOKEN='your-token'

ODOO_PASSWORD=$(vault kv get -field=password secret/mcp/odoo)
```

### API Key Rotation

```bash
# Rotate API keys regularly (script)
#!/bin/bash
NEW_KEY=$(openssl rand -hex 32)
OLD_KEY=$(grep "X-API-Key" /etc/nginx/sites-available/mcp-odoo | awk '{print $2}' | tr -d '";')

# Update Nginx config
sed -i "s/$OLD_KEY/$NEW_KEY/g" /etc/nginx/sites-available/mcp-odoo

# Test and reload
nginx -t && systemctl reload nginx

# Notify clients
echo "New API Key: $NEW_KEY" | mail -s "MCP API Key Rotated" admin@company.com
```

---

## Firewall Configuration

### UFW (Ubuntu/Debian)

```bash
# Default deny
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH access
sudo ufw allow 22/tcp

# HTTPS only (block direct HTTP/SSE access)
sudo ufw allow 443/tcp

# Block MCP ports from internet
sudo ufw deny 8008/tcp
sudo ufw deny 8009/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

### iptables

```bash
# Flush existing rules
iptables -F

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# HTTPS only
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Block MCP ports
iptables -A INPUT -p tcp --dport 8008 -j DROP
iptables -A INPUT -p tcp --dport 8009 -j DROP

# Save rules
iptables-save > /etc/iptables/rules.v4
```

---

## Incident Response

### Security Event Checklist

**1. Detection**
- [ ] Monitor logs for anomalies
- [ ] Set up automated alerts (Fail2ban, monitoring tools)
- [ ] Review failed authentication attempts

**2. Analysis**
- [ ] Identify attack source (IP addresses)
- [ ] Determine attack type (brute force, DoS, data exfiltration)
- [ ] Assess potential damage

**3. Containment**
- [ ] Block attacking IPs immediately
- [ ] Rotate compromised API keys
- [ ] Temporarily disable service if needed

**4. Recovery**
- [ ] Restore from backups if needed
- [ ] Verify data integrity
- [ ] Re-enable service with enhanced security

**5. Post-Incident**
- [ ] Document incident
- [ ] Update security measures
- [ ] Train team on lessons learned

### Emergency Response Commands

```bash
# Block IP immediately
sudo ufw deny from 203.0.113.50

# Rotate API key
NEW_KEY=$(openssl rand -hex 32)
sed -i "s/prod-api-key-[^\"]*/$NEW_KEY/g" /etc/nginx/sites-available/mcp-odoo
nginx -t && systemctl reload nginx

# Stop service
sudo systemctl stop mcp-odoo-http

# Review recent access
tail -n 1000 /var/log/nginx/mcp_access.log | grep "POST /mcp"

# Check for data exfiltration
grep -E "(search_read|read)" /var/log/nginx/mcp_access.log | awk '{print $1, $7}' | sort | uniq -c | sort -rn
```

---

## Compliance Considerations

### GDPR / Data Protection

- **Encryption in transit**: SSL/TLS for all connections
- **Access logging**: Track who accessed what data
- **Data minimization**: Only request necessary Odoo fields
- **Right to erasure**: Ability to delete user data

### SOC 2 / ISO 27001

- **Access control**: mTLS or API key authentication
- **Audit logs**: Comprehensive logging of all access
- **Incident response**: Documented procedures
- **Regular reviews**: Security audits and penetration testing

---

## Security Hardening Checklist

### Infrastructure

- [ ] Run MCP server as non-root user
- [ ] Bind to localhost only (127.0.0.1, not 0.0.0.0)
- [ ] Use reverse proxy (Nginx) for public access
- [ ] Enable SSL/TLS with strong ciphers
- [ ] Configure firewall (UFW/iptables)

### Authentication

- [ ] Implement authentication (API Key, Basic Auth, or mTLS)
- [ ] Rotate credentials regularly
- [ ] Use strong, unique API keys (32+ bytes random)
- [ ] Store secrets securely (environment variables, Vault)

### Access Control

- [ ] IP whitelisting for known networks
- [ ] Rate limiting to prevent abuse
- [ ] Principle of least privilege (Odoo user permissions)

### Monitoring

- [ ] Enable comprehensive logging
- [ ] Set up log rotation
- [ ] Monitor for failed authentication
- [ ] Alert on anomalous behavior
- [ ] Use Fail2ban for auto-blocking

### Maintenance

- [ ] Regular OS updates
- [ ] Keep Nginx up to date
- [ ] Update MCP server when new versions release
- [ ] Review and update security configurations quarterly

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Nginx Security Best Practices](https://www.nginx.com/blog/nginx-security-best-practices/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Fail2ban Documentation](https://www.fail2ban.org/wiki/index.php/Main_Page)
- [TRANSPORTS.md](TRANSPORTS.md) - Transport-specific security configs

---

**Last Updated**: 2025-01-10
**Version**: 1.0.0-beta.2
