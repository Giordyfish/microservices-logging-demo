# E-Commerce Microservices Observability Demo

Learn modern observability practices through a hands-on microservices demo featuring **OpenTelemetry**, **Grafana Loki**, **Tempo**, and **Prometheus**.

This project demonstrates production-ready patterns for structured logging, distributed tracing, and metrics in a Python FastAPI microservices architecture.

## What You'll Learn

✅ **Structured logging** with JSON formatting and contextual data
✅ **Distributed tracing** using OpenTelemetry and W3C Trace Context
✅ **Automatic trace propagation** across services (no manual header passing!)
✅ **Metrics collection** with Prometheus scraping /metrics endpoints
✅ **Log aggregation** with Grafana Loki and LogQL queries
✅ **Trace visualization** with Grafana Tempo
✅ **Correlating logs ↔ traces ↔ metrics** for powerful debugging

---

## Quick Start

### Prerequisites

- **Docker** and **Docker Compose**
- **Python 3.10+** (for local development)

### 1️⃣ Start the Stack

```bash
# Clone the repository
git clone <repo-url>
cd microservices-logging-demo

# Start all services
docker-compose up -d

# Watch the logs
docker-compose logs -f
```

### 2️⃣ Generate Test Traffic

Run the test script to create sample requests:

```bash
# Linux/Mac
./scripts/unix/test_services.sh

# Windows
./scripts/windows/test_services.bat
```

Or test manually:

```bash
# Get all products
curl http://localhost:8000/products

# Create an order
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2, "customer_name": "John Doe", "customer_email": "john@example.com"}'
```

### 3️⃣ Explore in Grafana

Open **Grafana** at [http://localhost:3000](http://localhost:3000) (credentials: `admin` / `admin`)

**View Logs:**

1. Go to **Explore** → Select **Loki** datasource
2. Try this query: `{service_name="api_gateway"}`

**View Traces:**

1. Go to **Explore** → Select **Tempo** datasource
2. Click **Search** → Filter by service name → Click on a trace

**Correlate Logs & Traces:**

1. Click on any span in a trace
2. Click the **Logs** button to see related logs

**View Metrics:**

1. Go to **Explore** → Select **Prometheus** datasource
2. Try queries like:
   - `rate(http_requests_total[5m])` - Request rate per second
   - `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` - 95th percentile latency

---

## Architecture

### System Overview

```
┌─────────┐
│ Client  │
└────┬────┘
     │
     ▼
┌─────────────────┐
│  API Gateway    │  :8000
│  (Entry Point)  │
└────┬─────────┬──┘
     │         │
     ▼         ▼
┌─────────┐ ┌──────────┐
│ Product │ │  Order   │
│ Service │ │ Service  │
│  :8001  │ │  :8002   │
└────┬────┘ └─────┬────┘
     │            │
     │ /metrics   │ /metrics
     │            │
     └─────┬──────┘
           │
    ┌──────┼────────────┐
    │      │            │
    │      ▼            ▼
    │  ┌─────────┐  ┌───────────┐
    │  │  OTEL   │  │Prometheus │
    │  │Collector│  │   :9090   │
    │  │  :4318  │  └────┬──────┘
    │  └──┬─────┬┘       │
    │     │     │        │
    │     ▼     ▼        │
    │  ┌────┐ ┌──────┐   │
    │  │Loki│ │Tempo │   │
    │  └──┬─┘ └───┬──┘   │
    │     │       │      │
    │     └───┬───┘      │
    │         ▼          │
    │    ┌─────────┐     │
    └───►│ Grafana │◄────┘
         │  :3000  │
         └─────────┘
```

### Services

| Service             | Port       | Purpose                                          |
| ------------------- | ---------- | ------------------------------------------------ |
| **API Gateway**     | 8000       | Entry point, routes requests to backend services |
| **Product Service** | 8001       | Manages product catalog and inventory            |
| **Order Service**   | 8002       | Handles order creation and tracking              |
| **OTEL Collector**  | 4317, 4318 | Receives telemetry (logs & traces) from services |
| **Loki**            | 3100       | Log aggregation and storage                      |
| **Tempo**           | 3200       | Distributed trace storage                        |
| **Prometheus**      | 9090       | Metrics scraping (scrapes /metrics endpoints)    |
| **Grafana**         | 3000       | Unified observability dashboard                  |

---

## Key Features

### 🔭 Three Pillars of Observability

This demo implements all three pillars of observability:

1. **📝 Logs (Loki)** - Structured JSON logs with trace context
2. **🔍 Traces (Tempo)** - Distributed tracing across services
3. **📊 Metrics (Prometheus)** - HTTP request metrics (rate, latency, errors)

All visualized together in **Grafana** for complete system insight.

### 🔍 Automatic Trace Propagation

No manual header passing required! OpenTelemetry instrumentation handles everything:

```python
# In API Gateway - trace context automatically propagated
async with httpx.AsyncClient() as client:
    response = await client.get(f"{PRODUCT_SERVICE_URL}/products")
    # ✨ W3C traceparent header added automatically by HTTPXClientInstrumentation
```

The same `trace_id` flows through: **API Gateway** → **Product Service** → **All logs**

### 📝 Structured Logging with Context

Every log includes rich contextual data:

```python
logger.info(
    "Order created successfully",
    extra={
        "order_id": order["id"],
        "product_id": product_id,
        "customer_name": order["customer_name"]
    }
)
```

Output (JSON format):

```json
{
  "timestamp": "2025-11-08T18:30:45.123Z",
  "level": "INFO",
  "message": "Order created successfully",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "a2d4e6f8b1c3d5a7",
  "order_id": 123,
  "product_id": 1,
  "customer_name": "John Doe"
}
```

### 🔗 Logs ↔ Traces Correlation

Click from logs to traces and back:

1. Find an error in Loki logs
2. Copy the `trace_id`
3. Search for it in Tempo to see the full request journey
4. Click on any span to see related logs

### 📊 Metrics with Prometheus

Services automatically expose metrics via `prometheus-fastapi-instrumentator`:

```python
# In each service's main.py
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, include_in_schema=False)
```

**Available metrics:**
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency histogram
- `http_request_size_bytes` - Request size
- `http_response_size_bytes` - Response size

Prometheus scrapes `/metrics` endpoint from each service every 15 seconds.

---

## Project Structure

```
microservices-logging-demo/
├── services/
│   ├── api_gateway/
│   │   ├── src/main.py         # Gateway routing logic
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── init.py             # Virtualenv setup
│   ├── product_service/
│   │   └── src/main.py         # Product catalog management
│   └── order_service/
│       └── src/main.py         # Order processing
│
├── shared/
│   └── logging/                # Shared logging library
│       ├── logger.py           # setup_logging() function
│       ├── filters.py          # Auto-inject trace_id/span_id
│       ├── formatters.py       # JSON & colored console formatters
│       └── tracing.py          # OpenTelemetry helpers
│
├── observability/
│   ├── otel-collector/
│   │   └── collector.yaml      # Routes logs→Loki, traces→Tempo
│   ├── loki/loki-config.yml
│   ├── tempo/tempo-config.yml
│   ├── prometheus/prometheus.yml
│   └── grafana/provisioning/   # Auto-provision datasources
│
├── scripts/
│   ├── unix/test_services.sh
│   └── windows/test_services.bat
│
├── docker-compose.yml          # Full stack orchestration
├── init-ws.py                  # Workspace initialization
└── README.md
```

---

## Example Scenarios

### 🐛 Scenario 1: Debug a Failed Order

**Problem:** Order creation fails for product ID 999

```bash
# Create an order for non-existent product
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"product_id": 999, "quantity": 1, "customer_name": "Jane", "customer_email": "jane@test.com"}'
```

**Solution in Grafana:**

1. Find error logs:

```logql
{service_name=~".+"} | level="ERROR"
```

2. Copy the `trace_id` from the error log

3. See all related logs across services:

```logql
{service_name=~".+"} | json | trace_id="<paste-trace-id>"
```

4. View the trace in Tempo to see exactly where it failed

### 📊 Scenario 2: Measure Service Performance

1. Open Grafana → **Explore** → **Tempo**
2. Search for traces from `api_gateway`
3. Analyze the trace timeline:
   - Total request duration
   - Time spent in each service
   - Identify bottlenecks

### 📦 Scenario 3: Track Inventory Changes

Monitor product stock updates:

```logql
{service_name="product_service"} |= "stock"
```

See all inventory changes across time with full context.

### 📈 Scenario 4: Analyze Performance with Metrics

1. Open Grafana → **Explore** → **Prometheus**
2. View overall request rate:
```promql
sum(rate(http_requests_total[5m])) by (handler)
```
3. Check error rates:
```promql
sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
```
4. Monitor 95th percentile latency:
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

---

## Development Guide

### Local Development (Without Docker)

```bash
# Initialize all service environments
python init-ws.py

# Terminal 1: API Gateway
cd services/api_gateway
source .venv/bin/activate
python src/main.py

# Terminal 2: Product Service
cd services/product_service
source .venv/bin/activate
python src/main.py

# Terminal 3: Order Service
cd services/order_service
source .venv/bin/activate
python src/main.py
```

### Adding a New Service

1. Create service directory: `services/my_service/`
2. Add `src/main.py` with FastAPI app
3. Create `requirements.txt` and `Dockerfile`
4. Copy `init.py` from existing service
5. Update `docker-compose.yml`
6. Instrument with OpenTelemetry:

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from shared.logging import setup_logging

logger = setup_logging("my_service")
FastAPIInstrumentor.instrument_app(app)
HTTPXClientInstrumentor().instrument()
```

### Useful LogQL Queries

```logql
# All logs from a specific service
{service_name="api_gateway"}

# Error logs across all services
{job=~".+"} | level="ERROR"

# Logs containing specific text
{service_name=~".+"} |= "order"

# Logs for a specific trace
{service_name=~".+"} | json | trace_id="<trace-id>"

# Count errors by service
sum by (service_name) (count_over_time({job=~".+"} | level="ERROR" [5m]))
```

---

## Why This Approach?

### OpenTelemetry vs Manual Correlation

| Feature               | Manual Correlation ID | OpenTelemetry                  |
| --------------------- | --------------------- | ------------------------------ |
| **Propagation**       | Manual header passing | ✅ Automatic (W3C standard)    |
| **Granularity**       | Request-level only    | ✅ Request + operation (spans) |
| **Compatibility**     | Custom per project    | ✅ Works with all OTEL tools   |
| **Maintenance**       | Update all services   | ✅ Library handles it          |
| **Visualization**     | None                  | ✅ Full trace timeline         |
| **Industry Standard** | No                    | ✅ Yes (W3C Trace Context)     |

### Structured Logging Benefits

**Old Way:**

```python
print(f"Order {order_id} created for {customer_name}")
```

❌ Hard to parse
❌ Difficult to search
❌ No standard format

**New Way:**

```python
logger.info("Order created", extra={"order_id": 123, "customer_name": "John"})
```

✅ Machine-readable (JSON)
✅ Easy to query in Loki
✅ Consistent format
✅ Automatic trace correlation

---

## Configuration

### Environment Variables

Configure services via environment variables in `docker-compose.yml`:

```yaml
environment:
  OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4318
  OTEL_SERVICE_NAME: api_gateway
  PRODUCT_SERVICE_URL: http://product-service:8001
  ORDER_SERVICE_URL: http://order-service:8002
```

### Service Ports

| Component       | Port | URL                   |
| --------------- | ---- | --------------------- |
| API Gateway     | 8000 | http://localhost:8000 |
| Product Service | 8001 | http://localhost:8001 |
| Order Service   | 8002 | http://localhost:8002 |
| Grafana         | 3000 | http://localhost:3000 |
| Prometheus      | 9090 | http://localhost:9090 |
| Loki API        | 3100 | http://localhost:3100 |
| Tempo API       | 3200 | http://localhost:3200 |

---

## Learn More

### Documentation

- [OpenTelemetry Docs](https://opentelemetry.io/docs/)
- [Grafana Loki Docs](https://grafana.com/docs/loki/latest/)
- [Grafana Tempo Docs](https://grafana.com/docs/tempo/latest/)
- [Prometheus Docs](https://prometheus.io/docs/)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)

### Key Concepts

- **Trace:** Complete journey of a request through your system
- **Span:** Single operation within a trace (e.g., database query, HTTP call)
- **trace_id:** Unique identifier for entire request flow
- **span_id:** Unique identifier for a specific operation
- **LogQL:** Loki's query language for searching logs
- **PromQL:** Prometheus Query Language for querying metrics

---

## Troubleshooting

### Services won't start

```bash
# Check if ports are already in use
docker ps

# View container logs
docker-compose logs <service-name>

# Restart a specific service
docker-compose restart <service-name>
```

### No traces appearing in Tempo

1. Check OTEL Collector is running: `docker-compose ps otel-collector`
2. Verify OTEL endpoint: `echo $OTEL_EXPORTER_OTLP_ENDPOINT`
3. Check collector logs: `docker-compose logs otel-collector`

### Logs not showing in Loki

1. Verify Loki is running: `curl http://localhost:3100/ready`
2. Check collector routing: See `observability/otel-collector/collector.yaml`
3. Test log ingestion: `docker-compose logs loki`

---

## Contributing

This is an educational project! Contributions welcome:

- 🚀 Add new microservices
- 📊 Create Grafana dashboards
- 📚 Improve documentation
- 🧪 Add integration tests
- 💡 Share your observability insights

---

## License

This project is open source and available for educational purposes.

## Next Steps

After exploring this demo:

1. ✅ Run the test scripts and explore Grafana
2. ✅ Practice writing LogQL queries
3. ✅ Try the example scenarios above
4. ✅ Add your own service following the patterns
5. ✅ Create custom Grafana dashboards
6. ✅ Experiment with different logging levels and contexts

**Happy learning! 🎉**
