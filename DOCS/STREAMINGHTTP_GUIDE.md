# StreamingHTTP Transport - Complete Guide

**Client → Server → Production Deployment**

This guide explains the Streamable HTTP transport for MCP at three levels: client implementation, server configuration, and production deployment.

---

## Table of Contents

- [Overview](#overview)
- [Client Level](#client-level)
- [Server Level](#server-level)
- [Production Deployment](#production-deployment)
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

## Production Deployment

For production, use the HTTP Docker image (`Dockerfile.http`) behind a TLS-terminating reverse proxy.

**Recommended stack:**
- Container: `alanogic/mcp-odoo-adv:http` on port 8008
- Reverse proxy: nginx (see [`nginx.conf.example`](../nginx.conf.example)) or Traefik
- Auth: Bearer token via [`run_server_http_secure.py`](../run_server_http_secure.py) — see [SECURITY.md](../SECURITY.md)
- Docker deployment details: [DOCKER.md](./DOCKER.md)

**Minimal docker run:**
```bash
docker run -d --name mcp-http \
  -p 127.0.0.1:8008:8008 \
  --env-file .env \
  --restart unless-stopped \
  alanogic/mcp-odoo-adv:http
```

Expose publicly through nginx on 443 with Let's Encrypt; never bind the container directly to 0.0.0.0 without auth.

---

## Complete Examples

### Example 1: Python Client → Remote Server

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
    # Connect to remote server
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

### Example 2: Node.js Client → Remote Server

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

# Tail container logs
docker logs -f mcp-http
```

**2. CORS Errors (Browser)**

Add to Nginx config:
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
- **Odoo API Reference**: https://www.odoo.com/documentation/

---

**You're now ready to deploy and use StreamingHTTP transport at all levels!** 🚀
