# StreamingHTTP Transport - Complete Guide

**Client → Server → Coolify Deployment**

This guide explains the Streamable HTTP transport for MCP at three levels: client implementation, server configuration, and production deployment with Coolify.

---

## Table of Contents

- [Overview](#overview)
- [Client Level](#client-level)
- [Server Level](#server-level)
- [Coolify Deployment](#coolify-deployment)
- [Complete Examples](#complete-examples)

---

## Overview

### What is StreamingHTTP Transport?

**StreamingHTTP** is a bidirectional streaming protocol over HTTP that:
- Works with standard HTTP/1.1 and HTTP/2
- Supports request/response streaming
- Compatible with any HTTP client (curl, fetch, httpx, requests)
- Ideal for server-to-server communication
- No WebSocket required

### Architecture

```
┌─────────────┐      HTTP POST      ┌─────────────┐      Odoo API      ┌─────────────┐
│   Client    │ ──────────────────> │ MCP Server  │ ─────────────────> │    Odoo     │
│ (Any HTTP)  │ <────────────────── │  (Python)   │ <───────────────── │  Instance   │
└─────────────┘   Streaming JSON    └─────────────┘   JSON-RPC/JSON-2  └─────────────┘
```

### Protocol Details

**Endpoint:** `http://host:port/mcp` (default: `http://0.0.0.0:8008/mcp`)

**Request Format:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "execute_method",
    "arguments": {
      "model": "res.partner",
      "method": "search_read",
      "kwargs_json": "{\"limit\": 10}"
    }
  },
  "id": 1
}
```

**Response Format:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "result": [...]
  },
  "id": 1
}
```

---

## Client Level

### 1. Python Client (httpx - Async)

**Installation:**
```bash
pip install httpx
```

**Basic Example:**
```python
import httpx
import json
import asyncio

async def call_mcp_tool(method_name, params):
    """Call an MCP tool via StreamingHTTP"""

    url = "http://localhost:8008/mcp"

    request_data = {
        "jsonrpc": "2.0",
        "method": method_name,
        "params": params,
        "id": 1
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30.0
        )

        return response.json()

# Example: List available tools
async def list_tools():
    result = await call_mcp_tool("tools/list", {})
    print(json.dumps(result, indent=2))

# Example: Execute Odoo method
async def search_partners():
    params = {
        "name": "execute_method",
        "arguments": {
            "model": "res.partner",
            "method": "search_read",
            "args_json": "[[]]",
            "kwargs_json": json.dumps({
                "fields": ["name", "email"],
                "limit": 5
            })
        }
    }

    result = await call_mcp_tool("tools/call", params)
    print(json.dumps(result, indent=2))

# Run examples
asyncio.run(list_tools())
asyncio.run(search_partners())
```

**Streaming Response Example:**
```python
import httpx
import json

async def stream_mcp_tool(method_name, params):
    """Call MCP tool and process streaming response"""

    url = "http://localhost:8008/mcp"

    request_data = {
        "jsonrpc": "2.0",
        "method": method_name,
        "params": params,
        "id": 1
    }

    async with httpx.AsyncClient() as client:
        async with client.stream(
            'POST',
            url,
            json=request_data,
            headers={'Content-Type': 'application/json'}
        ) as response:
            async for chunk in response.aiter_bytes():
                if chunk:
                    # Process each chunk as it arrives
                    print(chunk.decode('utf-8'))

# Use for large datasets
asyncio.run(stream_mcp_tool("tools/call", {...}))
```

### 2. Python Client (requests - Sync)

**Installation:**
```bash
pip install requests
```

**Example:**
```python
import requests
import json

def call_mcp_tool(method_name, params):
    """Synchronous MCP tool call"""

    url = "http://localhost:8008/mcp"

    request_data = {
        "jsonrpc": "2.0",
        "method": method_name,
        "params": params,
        "id": 1
    }

    response = requests.post(
        url,
        json=request_data,
        headers={"Content-Type": "application/json"},
        timeout=30
    )

    response.raise_for_status()
    return response.json()

# Example usage
result = call_mcp_tool("tools/list", {})
print(json.dumps(result, indent=2))

# Execute Odoo method
params = {
    "name": "execute_method",
    "arguments": {
        "model": "res.partner",
        "method": "search_count",
        "args_json": "[[]]"
    }
}

result = call_mcp_tool("tools/call", params)
print(f"Partner count: {result['result']['result']}")
```

### 3. JavaScript/TypeScript Client (Node.js)

**Installation:**
```bash
npm install node-fetch
```

**Example:**
```javascript
import fetch from 'node-fetch';

async function callMCPTool(methodName, params) {
  const url = 'http://localhost:8008/mcp';

  const requestData = {
    jsonrpc: '2.0',
    method: methodName,
    params: params,
    id: 1
  };

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestData)
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

// Example: List tools
async function listTools() {
  const result = await callMCPTool('tools/list', {});
  console.log(JSON.stringify(result, null, 2));
}

// Example: Search partners
async function searchPartners() {
  const params = {
    name: 'execute_method',
    arguments: {
      model: 'res.partner',
      method: 'search_read',
      args_json: '[[]]',
      kwargs_json: JSON.stringify({
        fields: ['name', 'email'],
        limit: 5
      })
    }
  };

  const result = await callMCPTool('tools/call', params);
  console.log(JSON.stringify(result, null, 2));
}

// Run examples
listTools();
searchPartners();
```

### 4. JavaScript Client (Browser)

**Example:**
```html
<!DOCTYPE html>
<html>
<head>
  <title>MCP Client</title>
</head>
<body>
  <h1>Odoo MCP Client</h1>
  <button onclick="listTools()">List Tools</button>
  <button onclick="searchPartners()">Search Partners</button>
  <pre id="output"></pre>

  <script>
    const MCP_URL = 'http://localhost:8008/mcp';

    async function callMCPTool(methodName, params) {
      const requestData = {
        jsonrpc: '2.0',
        method: methodName,
        params: params,
        id: 1
      };

      const response = await fetch(MCP_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      return await response.json();
    }

    async function listTools() {
      const result = await callMCPTool('tools/list', {});
      document.getElementById('output').textContent = JSON.stringify(result, null, 2);
    }

    async function searchPartners() {
      const params = {
        name: 'execute_method',
        arguments: {
          model: 'res.partner',
          method: 'search_read',
          args_json: '[[]]',
          kwargs_json: JSON.stringify({
            fields: ['name', 'email'],
            limit: 5
          })
        }
      };

      const result = await callMCPTool('tools/call', params);
      document.getElementById('output').textContent = JSON.stringify(result, null, 2);
    }
  </script>
</body>
</html>
```

### 5. cURL Client

**List tools:**
```bash
curl -X POST http://localhost:8008/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 1
  }' | jq
```

**Execute Odoo method:**
```bash
curl -X POST http://localhost:8008/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "execute_method",
      "arguments": {
        "model": "res.partner",
        "method": "search_read",
        "args_json": "[[]]",
        "kwargs_json": "{\"fields\": [\"name\", \"email\"], \"limit\": 5}"
      }
    },
    "id": 1
  }' | jq
```

**With authentication (API key):**
```bash
curl -X POST https://mcp.yourdomain.com/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key" \
  -d '{...}' | jq
```

---

## Server Level

### 1. How It Works

**Server Architecture:**
```python
# run_server_http.py

from src.odoo_mcp.server import mcp
import os

# Get configuration
host = os.environ.get("MCP_HOST", "0.0.0.0")  # Bind to all interfaces
port = int(os.environ.get("MCP_PORT", "8008"))  # Port 8008
path = os.environ.get("MCP_HTTP_PATH", "/mcp")  # Endpoint path

# Run server with StreamingHTTP transport
mcp.run(
    transport="streamable-http",  # Transport type
    host=host,                    # Bind address
    port=port,                    # Listen port
    path=path,                    # HTTP endpoint
)
```

**Request Flow:**
1. Client sends HTTP POST to `/mcp`
2. FastMCP receives request and parses JSON-RPC
3. MCP server validates and routes to tool
4. Tool executes (e.g., `execute_method` calls Odoo API)
5. Response streamed back to client as JSON-RPC

### 2. Configuration

**Environment Variables:**
```bash
# Server binding
MCP_HOST=0.0.0.0          # 0.0.0.0 = all interfaces, 127.0.0.1 = localhost only
MCP_PORT=8008             # HTTP server port
MCP_HTTP_PATH=/mcp        # Endpoint path

# Odoo connection
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password

# Optional
ODOO_TIMEOUT=30           # Request timeout
ODOO_VERIFY_SSL=true      # SSL verification
HTTP_PROXY=http://proxy   # Proxy for Odoo connection
DEBUG=0                   # Debug logging
```

### 3. Running the Server

**Local Development:**
```bash
# Standard run
python run_server_http.py

# Custom port
MCP_PORT=9000 python run_server_http.py

# Localhost only (more secure)
MCP_HOST=127.0.0.1 python run_server_http.py

# With debug logging
DEBUG=1 python run_server_http.py
```

**Docker:**
```bash
# Build
docker build -t mcp-odoo:http -f Dockerfile.http .

# Run
docker run -p 8008:8008 \
  -e ODOO_URL=https://demo.odoo.com \
  -e ODOO_DB=demo \
  -e ODOO_USERNAME=admin \
  -e ODOO_PASSWORD=admin \
  mcp-odoo:http

# Or with .env file
docker run -p 8008:8008 --env-file .env mcp-odoo:http
```

**Docker Compose:**
```yaml
# docker-compose.yml
services:
  mcp-http:
    image: alanogic/mcp-odoo-adv:http
    ports:
      - "8008:8008"
    environment:
      - ODOO_URL=https://your-instance.odoo.com
      - ODOO_DB=your-database
      - ODOO_USERNAME=your-username
      - ODOO_PASSWORD=your-password
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8008
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8008/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 4. Logging

**Server logs to:**
- `stderr` (console)
- `./logs/mcp_server_http_YYYYMMDD_HHMMSS.log` (file)

**View logs:**
```bash
# Real-time monitoring
tail -f logs/mcp_server_http_*.log

# Search for errors
grep -i error logs/mcp_server_http_*.log

# View last 100 lines
tail -n 100 logs/mcp_server_http_*.log
```

### 5. Health Check

**Endpoint:** `http://host:port/health`

```bash
curl http://localhost:8008/health
```

**Response:**
```json
{
  "status": "healthy",
  "transport": "streamable-http",
  "version": "1.0.0"
}
```

---

## Coolify Deployment

[Coolify](https://coolify.io) is a self-hosted Heroku/Netlify alternative. Here's how to deploy the MCP server.

### 1. Prerequisites

- Coolify instance running
- Docker installed on Coolify server
- Domain name (optional, for SSL)

### 2. Deployment Method 1: Docker Image

**Step 1: Create New Resource**
1. Log into Coolify dashboard
2. Click "New Resource"
3. Select "Docker Image"
4. Name: `odoo-mcp-http`

**Step 2: Configure Docker Image**
```
Image: alanogic/mcp-odoo-adv:http
Tag: latest
```

**Step 3: Port Mapping**
```
Container Port: 8008
Public Port: 8008
```

**Step 4: Environment Variables**

In Coolify, add these environment variables:
```bash
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password
MCP_HOST=0.0.0.0
MCP_PORT=8008
```

**Step 5: Health Check**
```
Path: /health
Port: 8008
Interval: 30s
```

**Step 6: Deploy**
1. Click "Save"
2. Click "Deploy"
3. Wait for deployment to complete

### 3. Deployment Method 2: Git Repository

**Step 1: Prepare Repository**

Create `coolify.json` in your repo:
```json
{
  "dockerComposeFile": "docker-compose.coolify.yml",
  "services": {
    "mcp-http": {
      "dockerfile": "Dockerfile.http",
      "buildArgs": {
        "PYTHON_VERSION": "3.13"
      }
    }
  }
}
```

Create `docker-compose.coolify.yml`:
```yaml
services:
  mcp-http:
    build:
      context: .
      dockerfile: Dockerfile.http
    ports:
      - "${PORT:-8008}:8008"
    environment:
      - ODOO_URL=${ODOO_URL}
      - ODOO_DB=${ODOO_DB}
      - ODOO_USERNAME=${ODOO_USERNAME}
      - ODOO_PASSWORD=${ODOO_PASSWORD}
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8008
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8008/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Step 2: Create Resource in Coolify**
1. Click "New Resource"
2. Select "Git Repository"
3. Connect your repository
4. Branch: `main` or `master`
5. Build Pack: Docker Compose

**Step 3: Environment Variables**
Add in Coolify dashboard:
```bash
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password
```

**Step 4: Deploy**
1. Click "Deploy"
2. Coolify builds and runs your Docker Compose

### 4. Domain & SSL Configuration

**Step 1: Add Domain**
1. In resource settings, go to "Domains"
2. Add domain: `mcp.yourdomain.com`
3. Coolify automatically provisions Let's Encrypt SSL

**Step 2: Update DNS**
```
Type: A
Name: mcp
Value: YOUR_COOLIFY_SERVER_IP
```

**Step 3: Access**
```
https://mcp.yourdomain.com/mcp
```

### 5. Reverse Proxy (Automatic in Coolify)

Coolify automatically configures:
- Nginx/Traefik reverse proxy
- SSL/TLS certificates
- HTTP → HTTPS redirect
- Health checks

**Manual Nginx Config (if needed):**
```nginx
# /etc/nginx/sites-available/mcp.yourdomain.com

upstream mcp_http {
    server 127.0.0.1:8008;
}

server {
    listen 80;
    server_name mcp.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mcp.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/mcp.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mcp.yourdomain.com/privkey.pem;

    location /mcp {
        proxy_pass http://mcp_http;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Streaming support
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_read_timeout 300s;
        client_max_body_size 100M;
    }

    location /health {
        proxy_pass http://mcp_http;
    }
}
```

### 6. Multiple Environments in Coolify

**Production + Staging Setup:**

```yaml
# docker-compose.coolify.yml

services:
  mcp-production:
    build:
      context: .
      dockerfile: Dockerfile.http
    ports:
      - "8008:8008"
    environment:
      - ODOO_CONFIG_DIR=/config/production
    volumes:
      - ./config:/config
    restart: unless-stopped

  mcp-staging:
    build:
      context: .
      dockerfile: Dockerfile.http
    ports:
      - "8009:8008"
    environment:
      - ODOO_CONFIG_DIR=/config/staging
    volumes:
      - ./config:/config
    restart: unless-stopped
```

**Directory structure:**
```
config/
├── production/
│   └── .env
└── staging/
    └── .env
```

**Access:**
- Production: `https://mcp.yourdomain.com:8008/mcp`
- Staging: `https://mcp.yourdomain.com:8009/mcp`

### 7. Monitoring in Coolify

**Built-in Metrics:**
- CPU usage
- Memory usage
- Network I/O
- Container logs

**Access Logs:**
```bash
# In Coolify dashboard
Resource → Logs → View Real-time Logs

# Or via CLI
coolify logs mcp-http

# Docker logs
docker logs -f mcp-http
```

### 8. Auto-Scaling (Coolify Pro)

```yaml
# docker-compose.coolify.yml with scaling

services:
  mcp-http:
    build:
      context: .
      dockerfile: Dockerfile.http
    deploy:
      replicas: 3  # Run 3 instances
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
      restart_policy:
        condition: on-failure
        max_attempts: 3
    ports:
      - "8008-8010:8008"
```

### 9. Backup & Restore

**Backup Environment Variables:**
```bash
# In Coolify dashboard
Resource → Environment → Export

# Or via CLI
coolify env:export mcp-http > mcp-env-backup.txt
```

**Restore:**
```bash
coolify env:import mcp-http < mcp-env-backup.txt
```

### 10. Security Best Practices for Coolify

**1. Use Secrets:**
```yaml
# docker-compose.coolify.yml
services:
  mcp-http:
    secrets:
      - odoo_password
    environment:
      - ODOO_PASSWORD_FILE=/run/secrets/odoo_password

secrets:
  odoo_password:
    external: true
```

**2. Network Isolation:**
```yaml
networks:
  mcp-network:
    driver: bridge
    internal: true  # No external access

services:
  mcp-http:
    networks:
      - mcp-network
```

**3. API Key Protection:**

Add middleware in Nginx/Traefik:
```nginx
# In Coolify custom Nginx config
location /mcp {
    # API key validation
    if ($http_x_api_key != "your-secret-key") {
        return 401;
    }

    proxy_pass http://mcp_http;
}
```

**4. Rate Limiting:**
```nginx
# In Coolify custom Nginx config
limit_req_zone $binary_remote_addr zone=mcp:10m rate=10r/s;

location /mcp {
    limit_req zone=mcp burst=20 nodelay;
    proxy_pass http://mcp_http;
}
```

---

## Complete Examples

### Example 1: Python Client → Coolify Server

**Client Code (`client.py`):**
```python
import httpx
import json
import asyncio

class MCPClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        self.endpoint = f"{base_url}/mcp"

    async def call_tool(self, method, params):
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.endpoint,
                headers=headers,
                json=request_data,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def execute_odoo(self, model, method, args_json="[]", kwargs_json="{}"):
        params = {
            "name": "execute_method",
            "arguments": {
                "model": model,
                "method": method,
                "args_json": args_json,
                "kwargs_json": kwargs_json
            }
        }
        return await self.call_tool("tools/call", params)

# Usage
async def main():
    # Connect to Coolify-deployed server
    client = MCPClient(
        base_url="https://mcp.yourdomain.com",
        api_key="your-secret-api-key"
    )

    # Search partners
    result = await client.execute_odoo(
        model="res.partner",
        method="search_read",
        kwargs_json=json.dumps({
            "fields": ["name", "email", "phone"],
            "limit": 10
        })
    )

    print(json.dumps(result, indent=2))

asyncio.run(main())
```

### Example 2: Node.js Client → Coolify Server

**Client Code (`client.js`):**
```javascript
import fetch from 'node-fetch';

class MCPClient {
  constructor(baseUrl, apiKey = null) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
    this.endpoint = `${baseUrl}/mcp`;
  }

  async callTool(method, params) {
    const headers = {
      'Content-Type': 'application/json'
    };

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }

    const requestData = {
      jsonrpc: '2.0',
      method: method,
      params: params,
      id: 1
    };

    const response = await fetch(this.endpoint, {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(requestData)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  async executeOdoo(model, method, argsJson = '[]', kwargsJson = '{}') {
    const params = {
      name: 'execute_method',
      arguments: {
        model: model,
        method: method,
        args_json: argsJson,
        kwargs_json: kwargsJson
      }
    };

    return await this.callTool('tools/call', params);
  }
}

// Usage
async function main() {
  const client = new MCPClient(
    'https://mcp.yourdomain.com',
    'your-secret-api-key'
  );

  // Create a new partner
  const result = await client.executeOdoo(
    'res.partner',
    'create',
    JSON.stringify([{
      name: 'Test Company',
      email: 'test@example.com'
    }])
  );

  console.log(JSON.stringify(result, null, 2));
}

main().catch(console.error);
```

### Example 3: Production Architecture

```
┌─────────────────┐
│   Internet      │
└────────┬────────┘
         │
         │ HTTPS (443)
         ↓
┌─────────────────┐
│  Cloudflare     │  ← DDoS protection, CDN
│  (Optional)     │
└────────┬────────┘
         │
         │
         ↓
┌─────────────────┐
│  Coolify +      │
│  Nginx/Traefik  │  ← SSL termination, rate limiting
│  (Reverse Proxy)│
└────────┬────────┘
         │
         │ HTTP (8008)
         ↓
┌─────────────────┐
│  MCP Server     │  ← StreamingHTTP transport
│  (Docker)       │
└────────┬────────┘
         │
         │ JSON-2 API
         ↓
┌─────────────────┐
│  Odoo Instance  │
└─────────────────┘
```

---

## Troubleshooting

### Common Issues

**1. Connection Refused**
```bash
# Check if server is running
curl http://localhost:8008/health

# Check Docker container
docker ps | grep mcp-odoo

# Check Coolify logs
coolify logs mcp-http
```

**2. CORS Errors (Browser)**

Add to Nginx config in Coolify:
```nginx
add_header Access-Control-Allow-Origin *;
add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS';
add_header Access-Control-Allow-Headers 'Content-Type, X-API-Key';
```

**3. 502 Bad Gateway**

Server not responding. Check:
```bash
# Container status
docker ps -a | grep mcp-odoo

# Logs
docker logs mcp-http

# Restart
docker restart mcp-http
```

**4. Authentication Errors**

```bash
# Test without auth
curl http://localhost:8008/mcp -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'

# Test with API key
curl https://mcp.yourdomain.com/mcp \
  -H "X-API-Key: your-key" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":1}'
```

---

## Additional Resources

- **FastMCP Documentation**: https://gofastmcp.com
- **MCP Specification**: https://modelcontextprotocol.io
- **Coolify Documentation**: https://coolify.io/docs
- **Odoo API Reference**: https://www.odoo.com/documentation/

---

**You're now ready to deploy and use StreamingHTTP transport at all levels!** 🚀
