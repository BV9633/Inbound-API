# API Backend Dockerfile

# Base OS Image
FROM python:3.13-slim 

# Set working directory
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app

# Update and upgrade system packages
RUN apt update && apt upgrade -y && apt --no-install-recommends install -y build-essential \
    python3 \
    python3-venv \
    build-essential \
    gcc \
    && apt clean && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/venv

# Install latest secure pip inside venv
RUN /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel

# Add venv to PATH
ENV PATH="/opt/venv/bin:$PATH"

# NOW that the venv is created and has its own secure pip, remove system-wide pip installations
RUN rm -rf /usr/share/python-wheels/pip* \
    && rm -rf /usr/lib/python3/dist-packages/pip* \
    && rm -rf /usr/local/lib/python*/dist-packages/pip* \
    && rm -rf /usr/local/lib/python*/site-packages/pip*

# Copy requirements first to cache dependencies
COPY deploy/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY --chown=root:root --chmod=755 main.py .
COPY --chown=root:root --chmod=755 cbp/ ./cbp/
COPY --chown=root:root --chmod=755 dashboard/ ./dashboard/
COPY --chown=root:root --chmod=755 exceptional/ ./exceptional/
COPY --chown=root:root --chmod=755 invoice/ ./invoice/
COPY --chown=root:root --chmod=755 users/ ./users/
COPY --chown=root:root --chmod=755 waybill/ ./waybill/
COPY --chown=root:root --chmod=755 age_calculator.py .
COPY --chown=root:root --chmod=755 parameterManager.py .
COPY --chown=root:root --chmod=755 secretManager.py .
COPY --chown=root:root --chmod=755 Service_imperson.py .

# Set read-only permissions on application code (except for necessary writable dirs)
USER root
RUN mkdir -p /app/logs /app/tmp && \
    chown appuser:appuser /app/logs /app/tmp && \
    chmod 755 /app/logs /app/tmp
USER appuser

EXPOSE 8080

# Command to run the fast appi script
CMD ["uvicorn", "main:app","--host", "0.0.0.0", "--port","8080"]