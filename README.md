# E-Commerce Microservices Observability Demo

A comprehensive, educational demonstration of microservices logging and observability using **Loki**, **Tempo**, **Grafana**, and **OpenTelemetry**.

This project implements a simple e-commerce platform with three microservices, showcasing best practices for structured logging, distributed tracing, and observability in a microservices architecture.

---

## Purpose

This demo is designed for **teaching and learning**:

- [x] How to implement structured logging in Python microservices
- [x] How to use OpenTelemetry for automatic distributed tracing
- [x] How trace_id and span_id automatically flow through services
- [x] How to aggregate logs with Grafana Loki
- [x] How to visualize traces with Grafana Tempo
- [x] How to correlate logs and traces in Grafana using trace_id

---

## Architecture

```
+---------------+
|    Client     |
+-------+-------+
        |
        v
+-------------------+
|   API Gateway     | :8000
|   (Service A)     |
+--------+----------+
         |
    +----+----------------+
    |                     |
    v                     v
+------------+    +--------------+
|  Product   |    |    Order     |
|  Service   |    |   Service    |
|(Service B) |    |  (Service C) |
|  :8001     |    |    :8002     |
+-----+------+    +------+-------+
      |                  |
      +--------+---------+
               |
        +------+----------+
        |                 |
        v                 v
+-------------+   +-------------+
|    Loki     |   |    Tempo    |
|   (Logs)    |   |  (Traces)   |
|   :3100     |   |   :3200     |
+------+------+   +------+------+
       |                 |
       +---------+-------+
                 |
          +------+-------+
          |   Grafana    |
          |    :3000     |
          +--------------+
```

### Services

1. **API Gateway** (Port 8000)
   - Entry point for all client requests
   - Routes requests to appropriate services
   - Initiates distributed traces with OpenTelemetry

2. **Product Service** (Port 8001)
   - Manages product catalog
   - Handles product queries and stock updates

3. **Order Service** (Port 8002)
   - Manages customer orders
   - Tracks order status

### Observability Stack

- **OpenTelemetry Collector** (Ports 4317, 4318)
  - Receives telemetry from services
  - Forwards logs to Loki and traces to Tempo

- **Grafana Loki** (Port 3100)
  - Log aggregation system
  - Stores and indexes logs

- **Grafana Tempo** (Port 3200)
  - Distributed tracing backend
  - Stores and queries traces

- **Grafana** (Port 3000)
  - Visualization and query interface
  - Correlates logs and traces

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local development)

### 1. Start the Stack

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

### 2. Access the Services

- **API Gateway**: http://localhost:8000
- **Product Service**: http://localhost:8001
- **Order Service**: http://localhost:8002
- **Grafana**: http://localhost:3000 (admin/admin)

### 3. Generate Sample Traffic

#### Option A: Use the Test Script (Recommended)

**Linux/Mac:**
```bash
./test_services.sh
```

**Windows PowerShell:**
```powershell
.\test_services.ps1
```

**Windows Command Prompt:**
```batch
test_services.bat
```

The test script will automatically run multiple tests to generate logs and traces.

#### Option B: Manual Testing

```bash
# Get all products
curl http://localhost:8000/products

# Get a specific product
curl http://localhost:8000/products/1

# Create an order
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2,
    "customer_name": "John Doe",
    "customer_email": "john@example.com"
  }'

# Get order details
curl http://localhost:8000/orders/1
```

### 4. Explore Logs in Grafana

1. Open Grafana: http://localhost:3000
2. Go to **Explore** (compass icon on left sidebar)
3. Select **Loki** datasource
4. Try these queries:

```logql
# All logs from API Gateway
{service_name="api_gateway"}

# Logs for a specific trace_id (replace with actual trace ID)
{service_name="api_gateway"} |= "trace_id" | json | trace_id="4bf92f3577b34da6a3ce929d0e0e4736"

# Error logs across all services
{job=~".+"} | level="ERROR"

# Logs related to orders
{job=~".+"} |= "order"
```

### 5. Explore Traces in Grafana

1. In Grafana **Explore**, select **Tempo** datasource
2. Click **Search** tab
3. Filter by service name (e.g., "api_gateway")
4. Click on a trace to see the full request flow across services

### 6. Correlate Logs and Traces

1. In a trace view, click on a span
2. Look for the **Logs** button
3. Click to see all logs related to that trace!

---

## Learning Guide

### Understanding the Code

#### 1. Structured Logging

The project uses a custom logging library in `shared/logging/`:

- **JSON Formatter**: Logs are structured as JSON for easy parsing
- **Colored Console**: Pretty console output for development
- **OTel Trace Filter**: Automatically adds trace_id and span_id to logs

Example from [services/api_gateway/main.py:132](services/api_gateway/main.py#L132):

```python
logger.info(
    "Products retrieved successfully",
    extra={"product_count": len(products)},
)
```

#### 2. OpenTelemetry Trace Context

Every log automatically includes `trace_id` and `span_id` from OpenTelemetry:

```python
# From shared/logging/filters.py - happens automatically!
trace_id = get_trace_id()  # Extracts from OpenTelemetry context
span_id = get_span_id()    # No manual header passing needed!

if trace_id:
    record.trace_id = trace_id  # Added to every log
if span_id:
    record.span_id = span_id
```

**Key Advantage**: W3C Trace Context headers are automatically propagated across services by OpenTelemetry instrumentation. No manual code required!

#### 3. Automatic Trace Propagation

OpenTelemetry automatically propagates trace context:

```python
# In api_gateway/main.py - NO manual header passing!
async with httpx.AsyncClient() as client:
    response = await client.get(
        f"{PRODUCT_SERVICE_URL}/products",
        # W3C traceparent header added automatically by HTTPXClientInstrumentation
    )
```

The trace flows: API Gateway → Product Service → All logs share the same trace_id!

#### 4. Log Levels

The code demonstrates different log levels:

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages (e.g., "Product not found")
- **ERROR**: Error messages with stack traces

#### 5. Context in Logs

Every log includes relevant context using the `extra` parameter:

```python
logger.info(
    "Order created successfully",
    extra={
        "order_id": order["id"],
        "product_id": product_id,
        "customer_name": order["customer_name"],
    },
)
```

This makes debugging much easier!

---

## Teaching Topics

### Topic 1: Why Structured Logging?

**Traditional logging:**
```python
print(f"Order {order_id} created for {customer_name}")
```
- [x] Hard to parse
- [x] Difficult to search
- [x] No standard format

**Structured logging:**
```python
logger.info("Order created", extra={"order_id": 123, "customer_name": "John"})
```
- [+] Machine-readable (JSON)
- [+] Easy to query in Loki
- [+] Consistent format

### Topic 2: OpenTelemetry Trace IDs (W3C Trace Context)

**The Problem:**
In microservices, a single user request might touch 3+ services. How do you track it?

**The Solution:**
OpenTelemetry automatically generates a `trace_id` and propagates it using W3C Trace Context headers (traceparent).

**How it works:**
1. FastAPIInstrumentation creates a span for each incoming request
2. HTTPXClientInstrumentation injects traceparent header into outgoing requests
3. All services extract trace context automatically
4. Every log gets trace_id and span_id injected automatically

**Benefits:**
- [+] Industry standard (works with Jaeger, Zipkin, Tempo, etc.)
- [+] Automatic propagation (no manual code!)
- [+] Get span_id too (more granular than correlation_id)
- [+] See the entire request journey across services
- [+] Click from logs → traces in Grafana

### Topic 3: Distributed Tracing

**What is a trace?**
A trace represents the journey of a request through your system.

**What is a span?**
A span represents a single operation within a trace (e.g., "call Product Service").

**Example trace for creating an order:**
```
Trace: Create Order Request
|- Span 1: API Gateway receives request
|- Span 2: API Gateway calls Product Service
|  `- Span 3: Product Service fetches product
|- Span 4: API Gateway calls Order Service
|  `- Span 5: Order Service creates order
`- Span 6: API Gateway returns response
```

### Topic 4: Observability Stack

```
Application -> OTEL Collector -> Loki (logs)  -> Grafana (visualization)
                               -> Tempo (traces) -^
```

1. **Services** emit logs and traces via OpenTelemetry
2. **OTEL Collector** receives and routes telemetry
3. **Loki** stores logs, **Tempo** stores traces
4. **Grafana** provides unified visualization

---

## Project Structure

```
microservices-logging-demo/
├── services/
│   ├── api_gateway/          # API Gateway service
│   │   ├── main.py           # FastAPI application
│   │   ├── Dockerfile        # Container definition
│   │   └── requirements.txt  # Python dependencies
│   ├── product_service/      # Product Service
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── order_service/        # Order Service
│       ├── main.py
│       ├── Dockerfile
│       └── requirements.txt
├── shared/
│   └── logging/              # Shared logging library
│       ├── __init__.py
│       ├── correlation.py    # Correlation ID utilities
│       ├── filters.py        # Logging filters
│       ├── formatters.py     # JSON and colored formatters
│       └── logger.py         # Main logger setup
├── observability/
│   ├── loki/
│   │   └── loki-config.yml   # Loki configuration
│   ├── tempo/
│   │   └── tempo-config.yml  # Tempo configuration
│   ├── otel-collector/
│   │   └── collector.yaml    # OTEL Collector config
│   └── grafana/
│       └── provisioning/     # Auto-provisioning configs
│           ├── datasources/
│           │   └── datasources.yml
│           └── dashboards/
│               └── dashboard.yml
├── docker-compose.yml        # Full stack definition
├── pyproject.toml            # Project dependencies
└── README.md                 # This file
```

---

## Example Scenarios

### Scenario 1: Track a Failed Order

1. Create an order for a non-existent product:
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"product_id": 999, "quantity": 1, "customer_name": "Jane", "customer_email": "jane@test.com"}'
```

2. In Grafana Loki, search for error logs:
```logql
{service_name=~".+"} | level="ERROR"
```

3. Find the trace_id in the error log (looks like: 4bf92f3577b34da6a3ce929d0e0e4736)
4. Search for all logs with that trace_id:
```logql
{service_name=~".+"} | json | trace_id="4bf92f3577b34da6a3ce929d0e0e4736"
```

5. See the entire request flow across all 3 services!
6. Click the trace_id to jump to Tempo and see the visual trace!

### Scenario 2: Measure Service Performance

1. In Grafana Tempo, search for traces from "api_gateway"
2. Look at the trace timeline to see:
   - How long each service took
   - Which service was the bottleneck
   - The complete call chain

### Scenario 3: Debug Stock Issues

1. Create multiple orders
2. Check product stock:
```bash
curl http://localhost:8001/products/1
```

3. In Grafana, search for stock-related logs:
```logql
{service_name="product_service"} |= "stock"
```

---

## Development

### Running Services Locally (without Docker)

```bash
# Install dependencies
pip install -e .

# Terminal 1: Start Product Service
cd services/product_service
python main.py

# Terminal 2: Start Order Service
cd services/order_service
python main.py

# Terminal 3: Start API Gateway
cd services/api_gateway
python main.py
```

### Viewing Logs

Logs are written to:
- **Console**: Colored, human-readable format
- **Files**: `logs/<service_name>/*.log` in JSON format

---

## Configuration

### Environment Variables

Each service supports these environment variables:

- `OTEL_EXPORTER_OTLP_ENDPOINT`: OTEL Collector URL (default: http://otel-collector:4318)
- `OTEL_SERVICE_NAME`: Service name for telemetry
- Log levels can be configured in the code

### Grafana Access

- **URL**: http://localhost:3000
- **Username**: admin
- **Password**: admin

---

## Additional Resources

### Learn More About:

- **OpenTelemetry**: https://opentelemetry.io/docs/
- **Grafana Loki**: https://grafana.com/docs/loki/latest/
- **Grafana Tempo**: https://grafana.com/docs/tempo/latest/
- **Structured Logging**: https://www.structlog.org/en/stable/why.html
- **Distributed Tracing**: https://opentelemetry.io/docs/concepts/observability-primer/#distributed-tracing

---

## Contributing

This is an educational project! Feel free to:

- Add new services
- Implement additional endpoints
- Create Grafana dashboards
- Add metrics (Prometheus)
- Improve documentation

---

## Key Takeaways

1. **Always use structured logging** - It makes debugging infinitely easier
2. **Include context in logs** - The `extra` parameter is your friend
3. **Use OpenTelemetry for tracing** - Industry standard, automatic propagation
4. **Leverage trace_id and span_id** - They're automatically added to every log
5. **Instrument with OTEL** - FastAPI and httpx instrumentation does the heavy lifting
6. **Centralize logs** - Loki makes searching across services trivial
7. **Correlate logs ↔ traces** - The ultimate debugging superpower

### Why OpenTelemetry trace_id > Manual correlation_id

| Aspect | Manual Correlation ID | OpenTelemetry trace_id |
|--------|----------------------|------------------------|
| Propagation | Manual header passing | Automatic (W3C standard) |
| Granularity | Request-level only | Request + operation (span_id) |
| Compatibility | Custom implementation | Works with all OTEL tools |
| Maintenance | Must update all services | Instrumentation handles it |
| Trace visualization | Not available | Full trace tree in Tempo |
| Industry standard | No | Yes (W3C Trace Context) |

---

## Next Steps

After exploring this demo:

1. [x] Understand how logs flow from service -> OTEL -> Loki -> Grafana
2. [x] Practice writing LogQL queries in Grafana
3. [x] Explore trace timelines in Tempo
4. [x] Try adding a new service with the same logging pattern
5. [x] Add custom dashboards in Grafana

Happy learning!
