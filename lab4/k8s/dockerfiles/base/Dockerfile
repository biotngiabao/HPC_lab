FROM python:3.10.12-slim
WORKDIR /app

# Copy requirements and install system build dependencies needed for some packages
COPY requirements.txt /app/requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc \
      libssl-dev \
      libffi-dev \
      python3-dev \
      cargo \
      procps && \
    rm -rf /var/lib/apt/lists/*

# Upgrade packaging tools to ensure wheels and metadata build correctly
RUN pip install --upgrade pip setuptools wheel

# Install Python requirements into the base image
RUN pip install --no-cache-dir -r /app/requirements.txt

ENV PYTHONUNBUFFERED=1

LABEL org.opencontainers.image.title="lab4-base"
LABEL org.opencontainers.image.description="Base image for lab4 services with system deps and Python requirements preinstalled"
