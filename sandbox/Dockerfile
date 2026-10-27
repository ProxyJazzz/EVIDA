# EVIDA Isolated Execution Sandbox Container
# Multi-stage hardened non-privileged execution environment

FROM python:3.12-slim-bookworm

# Set metadata
LABEL maintainer="EVIDA Core Systems Team"
LABEL description="Isolated execution boundary for EVIDA repair verification"

# Install minimal toolset required for test runners
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root unprivileged sandbox user
RUN groupadd -g 1000 sandboxgroup && \
    useradd -u 1000 -g sandboxgroup -m -s /bin/bash sandboxuser

# Create isolated working directory
WORKDIR /workspace
RUN chown -R sandboxuser:sandboxgroup /workspace

# Switch to unprivileged user
USER sandboxuser

# Set environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/sandboxuser/.local/bin:${PATH}"

# Default entrypoint
CMD ["python3", "-c", "print('EVIDA sandbox OK')"]
