# Docker Deployment Guide

**Containerized MCP Server for Odoo - Three Transport Options**

This guide covers building, running, and deploying the Odoo MCP Server using Docker containers.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Available Images](#available-images)
- [Building Images](#building-images)
- [Running Containers](#running-containers)
- [Configuration](#configuration)
- [Docker Compose](#docker-compose)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

---

## Quick Start

### 1. Prepare Environment File

```bash
# Copy example and configure
cp .env.example .env

# Edit with your Odoo credentials
vim .env
```

Required variables:
```bash
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password
```

### 2. Build and Run

**STDIO Transport (Claude Desktop):**
```bash
docker build -t mcp-odoo:stdio -f Dockerfile .
docker run -i --rm --env-file .env mcp-odoo:stdio
```

**SSE Transport (Web Browsers):**
```bash
docker build -t mcp-odoo:sse -f Dockerfile.sse .
docker run -p 8009:8009 --env-file .env mcp-odoo:sse
```

**HTTP Transport (API Integrations):**
```bash
docker build -t mcp-odoo:http -f Dockerfile.http .
docker run -p 8008:8008 --env-file .env mcp-odoo:http
```

---

## Available Images

### Official Images (Docker Hub)

Pre-built images are available at `alanogic/mcp-odoo-adv`:

```bash
# Pull images
docker pull alanogic/mcp-odoo-adv:latest      # STDIO transport
docker pull alanogic/mcp-odoo-adv:sse         # SSE transport
docker pull alanogic/mcp-odoo-adv:http        # HTTP transport

# Run immediately
docker run -i --rm --env-file .env alanogic/mcp-odoo-adv:latest
docker run -p 8009:8009 --env-file .env alanogic/mcp-odoo-adv:sse
docker run -p 8008:8008 --env-file .env alanogic/mcp-odoo-adv:http
```

### Transport Comparison

| Transport | Image Tag | Port | Use Case | Interactive |
|-----------|-----------|------|----------|-------------|
| **STDIO** | `latest` | - | Claude Desktop, CLI tools | Yes (`-i`) |
| **SSE** | `sse` | 8009 | Web browsers, streaming | No |
| **HTTP** | `http` | 8008 | API integrations, REST clients | No |

---

## Building Images

### Build All Transports

```bash
# STDIO (default)
docker build -t mcp-odoo:stdio -f Dockerfile .

# SSE
docker build -t mcp-odoo:sse -f Dockerfile.sse .

# HTTP
docker build -t mcp-odoo:http -f Dockerfile.http .
```

### Build with Specific Python Version

All Dockerfiles support Python 3.10-3.14:

```bash
# Python 3.13 (default in SSE/HTTP)
docker build -t mcp-odoo:stdio -f Dockerfile .

# Python 3.14 (bleeding edge)
docker build --build-arg PYTHON_VERSION=3.14 -t mcp-odoo:stdio -f Dockerfile .

# Python 3.10 (maximum compatibility)
docker build --build-arg PYTHON_VERSION=3.10 -t mcp-odoo:sse -f Dockerfile.sse .
```

### Build Optimization

Docker images use multi-layer caching for fast rebuilds:

```bash
# Layer 1: System dependencies (rarely changes)
# Layer 2: Python dependencies (changes when pyproject.toml updates)
# Layer 3: Source code (changes frequently)

# First build: ~2-3 minutes
docker build -t mcp-odoo:stdio .

# Subsequent builds (code changes only): ~10-15 seconds
docker build -t mcp-odoo:stdio .
```

### Tag for Docker Hub

```bash
# Build and tag for publishing
docker build -t alanogic/mcp-odoo-adv:latest -f Dockerfile .
docker build -t alanogic/mcp-odoo-adv:sse -f Dockerfile.sse .
docker build -t alanogic/mcp-odoo-adv:http -f Dockerfile.http .

# Push to Docker Hub
docker push alanogic/mcp-odoo-adv:latest
docker push alanogic/mcp-odoo-adv:sse
docker push alanogic/mcp-odoo-adv:http
```

---

## Running Containers

### STDIO Transport

**For Claude Desktop integration:**

```bash
# Interactive mode (required for STDIO)
docker run -i --rm --env-file .env mcp-odoo:stdio

# With inline environment variables
docker run -i --rm \
  -e ODOO_URL=https://demo.odoo.com \
  -e ODOO_DB=demo \
  -e ODOO_USERNAME=admin \
  -e ODOO_PASSWORD=admin \
  mcp-odoo:stdio

# Named container (persistent)
docker run -i --name odoo-mcp --env-file .env mcp-odoo:stdio

# Stop named container
docker stop odoo-mcp
docker rm odoo-mcp
```

**Claude Desktop Configuration:**

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "ODOO_URL=https://your-instance.odoo.com",
        "-e", "ODOO_DB=your-database",
        "-e", "ODOO_USERNAME=your-username",
        "-e", "ODOO_PASSWORD=your-password",
        "alanogic/mcp-odoo-adv:latest"
      ]
    }
  }
}
```

Or with `.env` file:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "--env-file", "/absolute/path/to/.env",
        "alanogic/mcp-odoo-adv:latest"
      ]
    }
  }
}
```

### SSE Transport

**For web browser connections:**

```bash
# Standard run
docker run -p 8009:8009 --env-file .env mcp-odoo:sse

# Background (daemon) mode
docker run -d -p 8009:8009 --env-file .env --name odoo-mcp-sse mcp-odoo:sse

# Check logs
docker logs -f odoo-mcp-sse

# Stop daemon
docker stop odoo-mcp-sse
docker rm odoo-mcp-sse
```

**Test SSE Endpoint:**

```bash
# Health check
curl http://localhost:8009/health

# SSE stream (keeps connection open)
curl -N http://localhost:8009/sse
```

### HTTP Transport

**For API integrations:**

```bash
# Standard run
docker run -p 8008:8008 --env-file .env mcp-odoo:http

# Background mode with restart policy
docker run -d \
  -p 8008:8008 \
  --env-file .env \
  --name odoo-mcp-http \
  --restart unless-stopped \
  mcp-odoo:http

# View logs
docker logs -f odoo-mcp-http
```

**Test HTTP Endpoint:**

```bash
# Health check
curl http://localhost:8008/health

# MCP endpoint
curl -X POST http://localhost:8008/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'
```

---

## Configuration

### Environment Variables

**Required:**
```bash
ODOO_URL=https://your-instance.odoo.com
ODOO_DB=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password
```

**Optional:**
```bash
# Custom configuration directory (highest priority)
ODOO_CONFIG_DIR=~/mcp-odoo-env           # Custom directory for .env file
# ODOO_CONFIG_DIR=/etc/odoo-mcp          # Or system-wide config

# Odoo API configuration
ODOO_API_VERSION=json-2                  # "json-2" (Odoo 19+) or "json-rpc" (default)
ODOO_API_KEY=your_api_key                # For JSON-2 API (replaces password)
ODOO_TIMEOUT=30                          # Connection timeout (default: 30s)
ODOO_VERIFY_SSL=true                     # SSL verification (default: true)

# Network proxy
HTTP_PROXY=http://proxy:8080             # HTTP proxy for Odoo connection

# Server configuration (SSE/HTTP only)
MCP_HOST=0.0.0.0                         # Bind address (default: 0.0.0.0)
MCP_PORT=8009                            # Port for SSE (default: 8009)
MCP_PORT=8008                            # Port for HTTP (default: 8008)

# Debugging
DEBUG=1                                  # Enable debug logging
```

### Using Custom Config Directory

**Organize multiple environments:**

```bash
# Create directory structure
mkdir -p ~/mcp-odoo-env/{production,staging,development}

# Configure each environment
cat > ~/mcp-odoo-env/production/.env << 'EOF'
ODOO_URL=https://production.odoo.com
ODOO_DB=prod-db
ODOO_USERNAME=admin
ODOO_PASSWORD=prod-password
EOF

cat > ~/mcp-odoo-env/staging/.env << 'EOF'
ODOO_URL=https://staging.odoo.com
ODOO_DB=staging-db
ODOO_USERNAME=admin
ODOO_PASSWORD=staging-password
EOF

# Run with specific environment
docker run -i --rm \
  -e ODOO_CONFIG_DIR=/config/production \
  -v ~/mcp-odoo-env:/config \
  alanogic/mcp-odoo-adv:latest
```

**Docker Compose with custom config:**

```yaml
services:
  odoo-mcp-production:
    image: alanogic/mcp-odoo-adv:sse
    environment:
      - ODOO_CONFIG_DIR=/config/production
    volumes:
      - ~/mcp-odoo-env:/config
    ports:
      - "8009:8009"

  odoo-mcp-staging:
    image: alanogic/mcp-odoo-adv:sse
    environment:
      - ODOO_CONFIG_DIR=/config/staging
    volumes:
      - ~/mcp-odoo-env:/config
    ports:
      - "8010:8009"
```

### Using .env File

**Method 1: Mount .env file**
```bash
docker run -i --rm --env-file /path/to/.env mcp-odoo:stdio
```

**Method 2: Mount as volume (not recommended - use --env-file)**
```bash
docker run -i --rm -v $(pwd)/.env:/app/.env mcp-odoo:stdio
```

**Method 3: Inline environment variables**
```bash
docker run -i --rm \
  -e ODOO_URL=https://demo.odoo.com \
  -e ODOO_DB=demo \
  -e ODOO_USERNAME=admin \
  -e ODOO_PASSWORD=admin \
  mcp-odoo:stdio
```

### Persistent Logs

Mount logs directory to persist across container restarts:

```bash
# Create local logs directory
mkdir -p ./logs

# Mount logs volume
docker run -p 8009:8009 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  mcp-odoo:sse

# Logs are now saved to ./logs/mcp_server_*.log
```

---

## Docker Compose

### Single Transport

**docker-compose.stdio.yml:**
```yaml
services:
  odoo-mcp-stdio:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        PYTHON_VERSION: 3.13
    env_file: .env
    stdin_open: true  # Required for STDIO
    tty: true
    volumes:
      - ./logs:/app/logs
```

Run:
```bash
docker compose -f docker-compose.stdio.yml up
```

**docker-compose.sse.yml:**
```yaml
services:
  odoo-mcp-sse:
    build:
      context: .
      dockerfile: Dockerfile.sse
      args:
        PYTHON_VERSION: 3.13
    env_file: .env
    ports:
      - "8009:8009"
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8009/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run:
```bash
docker compose -f docker-compose.sse.yml up -d
```

**docker-compose.http.yml:**
```yaml
services:
  odoo-mcp-http:
    build:
      context: .
      dockerfile: Dockerfile.http
      args:
        PYTHON_VERSION: 3.13
    env_file: .env
    ports:
      - "8008:8008"
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8008/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run:
```bash
docker compose -f docker-compose.http.yml up -d
```

### All Transports Together

**docker-compose.yml:**
```yaml
services:
  # SSE Transport
  odoo-mcp-sse:
    build:
      context: .
      dockerfile: Dockerfile.sse
    env_file: .env
    ports:
      - "8009:8009"
    volumes:
      - ./logs/sse:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8009/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # HTTP Transport
  odoo-mcp-http:
    build:
      context: .
      dockerfile: Dockerfile.http
    env_file: .env
    ports:
      - "8008:8008"
    volumes:
      - ./logs/http:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8008/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run:
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

---

## Production Deployment

### Best Practices

**1. Use Secrets for Credentials**

Never commit `.env` to version control. Use Docker secrets or environment variables:

```bash
# Docker Swarm secrets
echo "your-password" | docker secret create odoo_password -

# Reference in service
docker service create \
  --name odoo-mcp \
  --secret odoo_password \
  -e ODOO_PASSWORD_FILE=/run/secrets/odoo_password \
  alanogic/mcp-odoo-adv:sse
```

**2. Health Checks**

Add health checks to monitor container status:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8009/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

**3. Resource Limits**

Prevent resource exhaustion:

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

**4. Logging**

Configure log rotation:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**5. Network Isolation**

Use custom networks for security:

```yaml
networks:
  odoo-mcp-network:
    driver: bridge

services:
  odoo-mcp-sse:
    networks:
      - odoo-mcp-network
```

### Production Docker Compose

**docker-compose.prod.yml:**
```yaml
services:
  odoo-mcp-sse:
    image: alanogic/mcp-odoo-adv:sse
    env_file: .env
    ports:
      - "8009:8009"
    volumes:
      - logs:/app/logs
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8009/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - odoo-mcp-network

  odoo-mcp-http:
    image: alanogic/mcp-odoo-adv:http
    env_file: .env
    ports:
      - "8008:8008"
    volumes:
      - logs:/app/logs
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8008/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - odoo-mcp-network

volumes:
  logs:

networks:
  odoo-mcp-network:
    driver: bridge
```

Deploy:
```bash
docker compose -f docker-compose.prod.yml up -d
```

### Reverse Proxy (Nginx)

**nginx.conf:**
```nginx
upstream odoo_mcp_sse {
    server localhost:8009;
}

upstream odoo_mcp_http {
    server localhost:8008;
}

server {
    listen 80;
    server_name mcp.example.com;

    # SSE endpoint
    location /sse {
        proxy_pass http://odoo_mcp_sse;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_cache off;
    }

    # HTTP endpoint
    location /mcp {
        proxy_pass http://odoo_mcp_http;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health checks
    location /health {
        proxy_pass http://odoo_mcp_sse;
    }
}
```

### SSL/TLS with Let's Encrypt

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d mcp.example.com

# Auto-renewal (crontab)
0 0 * * * certbot renew --quiet
```

---

## Troubleshooting

### Common Issues

**1. Container exits immediately**

Check logs:
```bash
docker logs <container_id>

# Or for compose
docker compose logs odoo-mcp-sse
```

**2. Connection refused**

Verify port mapping:
```bash
# Check if port is exposed
docker ps

# Check if service is listening inside container
docker exec <container_id> netstat -tulpn | grep 8009
```

**3. Authentication failures**

Test credentials:
```bash
# Run interactively to see errors
docker run -it --env-file .env mcp-odoo:stdio

# Or check environment inside container
docker exec <container_id> env | grep ODOO
```

**4. Image build fails**

Clear build cache:
```bash
# Remove build cache
docker builder prune -a

# Rebuild without cache
docker build --no-cache -t mcp-odoo:stdio .
```

**5. Permission denied on logs**

Fix logs directory permissions:
```bash
# Make logs writable
chmod 777 ./logs

# Or run container as current user
docker run --user $(id -u):$(id -g) -p 8009:8009 --env-file .env mcp-odoo:sse
```

### Debug Mode

Enable debug logging:

```bash
docker run -p 8009:8009 \
  --env-file .env \
  -e DEBUG=1 \
  mcp-odoo:sse
```

### Interactive Shell

Access container shell for debugging:

```bash
# Run with shell
docker run -it --env-file .env --entrypoint /bin/bash mcp-odoo:stdio

# Or access running container
docker exec -it <container_id> /bin/bash

# Inside container
python -m odoo_mcp  # Test manually
env | grep ODOO     # Check environment
```

---

## Advanced Usage

### Multi-Stage Builds (Future)

For smaller production images:

```dockerfile
# Build stage
FROM python:3.13-slim AS builder
WORKDIR /app
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir build && python -m build

# Production stage
FROM python:3.13-slim
WORKDIR /app
COPY --from=builder /app/dist/*.whl ./
RUN pip install --no-cache-dir *.whl
ENTRYPOINT ["python", "-m", "odoo_mcp"]
```

### Custom Entrypoint

Override entrypoint for testing:

```bash
# Use custom script
docker run -it \
  --env-file .env \
  --entrypoint python \
  mcp-odoo:stdio \
  -c "from odoo_mcp.odoo_client import get_odoo_client; print(get_odoo_client())"
```

### Docker Swarm Deployment

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml odoo-mcp

# Scale service
docker service scale odoo-mcp_odoo-mcp-sse=3

# View services
docker service ls
docker service logs odoo-mcp_odoo-mcp-sse
```

### Kubernetes Deployment

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: odoo-mcp-sse
spec:
  replicas: 2
  selector:
    matchLabels:
      app: odoo-mcp-sse
  template:
    metadata:
      labels:
        app: odoo-mcp-sse
    spec:
      containers:
      - name: odoo-mcp-sse
        image: alanogic/mcp-odoo-adv:sse
        ports:
        - containerPort: 8009
        env:
        - name: ODOO_URL
          valueFrom:
            secretKeyRef:
              name: odoo-credentials
              key: url
        - name: ODOO_DB
          valueFrom:
            secretKeyRef:
              name: odoo-credentials
              key: database
        - name: ODOO_USERNAME
          valueFrom:
            secretKeyRef:
              name: odoo-credentials
              key: username
        - name: ODOO_PASSWORD
          valueFrom:
            secretKeyRef:
              name: odoo-credentials
              key: password
        livenessProbe:
          httpGet:
            path: /health
            port: 8009
          initialDelaySeconds: 10
          periodSeconds: 30
        resources:
          limits:
            cpu: "1"
            memory: "512Mi"
          requests:
            cpu: "500m"
            memory: "256Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: odoo-mcp-sse
spec:
  selector:
    app: odoo-mcp-sse
  ports:
  - protocol: TCP
    port: 8009
    targetPort: 8009
  type: LoadBalancer
```

Deploy:
```bash
# Create secret
kubectl create secret generic odoo-credentials \
  --from-literal=url=https://demo.odoo.com \
  --from-literal=database=demo \
  --from-literal=username=admin \
  --from-literal=password=admin

# Deploy
kubectl apply -f deployment.yaml

# Check status
kubectl get pods
kubectl logs -f deployment/odoo-mcp-sse
```

---

## Image Sizes

Approximate image sizes after build:

| Transport | Size | Layers |
|-----------|------|--------|
| STDIO | ~180 MB | 8 |
| SSE | ~175 MB | 7 |
| HTTP | ~175 MB | 7 |

Size breakdown:
- Python 3.13-slim base: ~125 MB
- Dependencies (FastMCP, requests): ~40 MB
- Source code: ~5 MB
- System packages (gcc, procps): ~10 MB

---

## Security Considerations

1. **Never commit .env files** - Use `.gitignore`
2. **Use secrets management** - Docker secrets, Kubernetes secrets, or env files outside repo
3. **Limit container capabilities** - Run as non-root user (future improvement)
4. **Scan images for vulnerabilities** - Use `docker scan` or Trivy
5. **Keep base images updated** - Rebuild regularly for security patches
6. **Use SSL/TLS** - Always use HTTPS for Odoo connections
7. **Network isolation** - Use custom networks, firewall rules
8. **Resource limits** - Prevent DoS attacks

---

## Performance Tuning

### CPU Optimization

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'  # Allow using 2 cores
```

### Memory Optimization

```bash
# Monitor memory usage
docker stats <container_id>

# Set memory limit
docker run --memory="512m" --memory-swap="1g" -p 8009:8009 --env-file .env mcp-odoo:sse
```

### Connection Pooling

Odoo MCP Server reuses connections automatically. No additional configuration needed.

---

## References

- **Dockerfile Reference**: https://docs.docker.com/reference/dockerfile/
- **Docker Compose**: https://docs.docker.com/compose/
- **Docker Security**: https://docs.docker.com/engine/security/
- **FastMCP**: https://gofastmcp.com
- **Odoo Documentation**: https://www.odoo.com/documentation/

---

**Connect AI to Odoo with Docker. Simple. Powerful. Production-ready.** 🐳
