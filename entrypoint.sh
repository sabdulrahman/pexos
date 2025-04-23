#!/bin/bash
set -e

# Create Python site-packages directory if it doesn't exist
mkdir -p /opt/venv/lib/python3.10/site-packages

# Check if pip is installed and install required packages
pip install numpy pandas

# Execute the command
exec "$@"
