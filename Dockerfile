# Odoo MCP Server — STDIO transport
# Build: docker build -t alanogic/mcp-odoo-adv:latest .
# Run:   docker run -i --rm --env-file .env alanogic/mcp-odoo-adv:latest

ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Dependency layer — cached until pyproject.toml changes
COPY pyproject.toml README.md /app/
RUN pip install --upgrade --no-cache-dir pip \
 && pip install --no-cache-dir "fastmcp[cli]>=2.12.0" requests python-dotenv

# Source layer
COPY src/ /app/src/
COPY fastmcp.json /app/

# Install as package so console scripts (odoo-mcp, odoo-mcp-http, ...) work
RUN pip install --no-cache-dir -e .

RUN mkdir -p /app/logs && chmod 777 /app/logs

ENV DEBUG="0"
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["odoo-mcp"]
