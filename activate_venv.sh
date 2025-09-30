#!/bin/bash
# Helper script to activate virtual environment

if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
    echo "Virtual environment activated!"
    echo "Python: $(which python3)"
    echo "Pip: $(which pip3)"
    echo ""
    echo "To run the server:"
    echo "  1. odoo-mcp                    # Standard entry point"
    echo "  2. python3 run_server.py       # With enhanced logging"
    echo "  3. python3 -m odoo_mcp         # Module mode"
else
    echo "Error: .venv directory not found"
    echo "Run: python3 -m venv .venv && source .venv/bin/activate && pip3 install -e '.[dev]'"
    exit 1
fi