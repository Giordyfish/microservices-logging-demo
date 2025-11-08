# Dockerfile for API Gateway Service
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install service dependencies
COPY services/api_gateway/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

# Install shared utilities package
COPY shared /shared
RUN pip install --no-cache-dir /shared && rm -rf /shared

# Copy application source
COPY services/api_gateway/src ./src

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "src/main.py"]
