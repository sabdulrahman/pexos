# Build stage for nsjail
FROM debian:buster-slim as nsjail-builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y \
    bison \
    flex \
    gcc \
    g++ \
    git \
    libprotobuf-dev \
    libnl-route-3-dev \
    libtool \
    make \
    pkg-config \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Clone and build nsjail
WORKDIR /tmp
RUN git clone https://github.com/google/nsjail.git && \
    cd nsjail && \
    make && \
    cp nsjail /usr/local/bin/

# Python base with required libraries
FROM python:3.10-slim-buster

# Copy nsjail from the builder stage
COPY --from=nsjail-builder /usr/local/bin/nsjail /usr/local/bin/
# Copy required libraries from the builder stage
COPY --from=nsjail-builder /usr/lib/*/libprotobuf.so* /usr/lib/
COPY --from=nsjail-builder /lib/*/libnl-route-3.so* /lib/

# Create lib64 directory if it doesn't exist (for ARM compatibility)
RUN mkdir -p /lib64

# Install runtime dependencies for nsjail
RUN apt-get update && \
    apt-get install -y \
    libprotobuf-dev \
    libnl-route-3-200 \
    && rm -rf /var/lib/apt/lists/*

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set up the entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Set up the Python environment
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py executor.py nsjail.config ./

# Expose the API port
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]