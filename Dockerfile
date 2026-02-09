FROM n8nio/n8n:latest

USER root

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    git \
    curl \
    unzip \
    jq \
    bash \
    openssh-client

# Install Terraform
ENV TERRAFORM_VERSION=1.5.7
RUN curl -LO "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip" && \
    unzip "terraform_${TERRAFORM_VERSION}_linux_amd64.zip" -d /usr/local/bin/ && \
    rm "terraform_${TERRAFORM_VERSION}_linux_amd64.zip"

# Install AWS CLI
RUN apk add --no-cache aws-cli

# Create a virtual environment for Python packages to avoid conflicts
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switch back to n8n user
USER node

# Set working directory
WORKDIR /data

# Expose n8n port
EXPOSE 5678
