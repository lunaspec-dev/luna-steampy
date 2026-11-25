# Luna-Steampy Python Application Dockerfile
# Containerized Steam API Explorer with database integration

FROM python:3.12

LABEL maintainer="Luna"

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY program/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy program files
COPY program/ .

# Expose port if running a server (optional, for future API server)
EXPOSE 5000

# Default command - bash for manual testing
CMD ["/bin/bash"]
