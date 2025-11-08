# Dockerfile for Order Service
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install service dependencies
COPY services/order_service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

# Install shared utilities package
COPY shared /shared
RUN pip install --no-cache-dir /shared && rm -rf /shared

# Copy application source
COPY services/order_service/src ./src

# Expose port
EXPOSE 8002

# Run the application
CMD ["python", "src/main.py"]
