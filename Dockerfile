# Supports Python 3.10-3.13, using 3.12 as stable baseline
# To use Python 3.13: docker build --build-arg PYTHON_VERSION=3.13 -t alanogic/mcp-odoo-adv:latest .
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

# Install system dependencies (cached layer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (for better caching)
COPY pyproject.toml README.md /app/

# Install Python dependencies (cached layer if pyproject.toml unchanged)
RUN pip install --no-cache-dir "fastmcp[cli]>=2.12.0" requests

# Copy source code (only invalidates this layer and below when code changes)
COPY src/ /app/src/
COPY run_server.py /app/
COPY fastmcp.json /app/

# Install package in editable mode (fast - no dependencies to install)
RUN pip install --no-cache-dir -e .

# Create logs directory
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Prefer ".env" file | Set environment variables (can be overridden at runtime)
# ENV ODOO_URL=""
#ENV ODOO_DB=""
#ENV ODOO_USERNAME=""
## ENV ODOO_PASSWORD=""
#ENV ODOO_TIMEOUT="30"
#ENV ODOO_VERIFY_SSL="1"
ENV DEBUG="0"

# Make run_server.py executable
RUN chmod +x run_server.py

# Set stdout/stderr to unbuffered mode
ENV PYTHONUNBUFFERED=1

# Run the custom MCP server script instead of the module
ENTRYPOINT ["python", "run_server.py"]
