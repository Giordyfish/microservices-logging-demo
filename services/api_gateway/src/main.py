"""
API Gateway Service for E-Commerce Platform

This service acts as the entry point for all client requests.
It routes requests to the appropriate microservices (Product Service, Order Service).


"""
import os
from fastapi import FastAPI, HTTPException
import httpx
from contextlib import asynccontextmanager

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
import sys
from pathlib import Path

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator


def _ensure_repo_root_on_path():
    """If running from source without installing shared, add repo root to sys.path."""
    current = Path(__file__).resolve()
    for _ in range(5):
        current = current.parent
        if (current / "shared").exists():
            if str(current) not in sys.path:
                sys.path.insert(0, str(current))
            break


try:
    from shared.logging import setup_logging
except ModuleNotFoundError:
    _ensure_repo_root_on_path()
    from shared.logging import setup_logging

# Service configuration
SERVICE_NAME = "api_gateway"
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

# Initialize OpenTelemetry
resource = Resource.create({"service.name": SERVICE_NAME})
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)

# Configure OTLP exporter to send traces to Tempo via OTEL Collector
otlp_exporter = OTLPSpanExporter(endpoint=f"{OTEL_ENDPOINT}/v1/traces")
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)

# Initialize logger (will automatically pick up trace_id and span_id)
logger = setup_logging(SERVICE_NAME, console_level="DEBUG", enable_file_logging=True)

# Service URLs (will be overridden by environment variables in Docker)
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8001")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8002")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    Runs startup and shutdown logic.
    """
    # Startup
    logger.info(
        "API Gateway starting up",
        extra={
            "product_service_url": PRODUCT_SERVICE_URL,
            "order_service_url": ORDER_SERVICE_URL,
            "otel_endpoint": OTEL_ENDPOINT,
        },
    )
    yield
    # Shutdown
    logger.info("API Gateway shutting down")
    # Ensure all spans are exported before shutdown
    tracer_provider.force_flush()


# Create FastAPI app
app = FastAPI(
    title="E-Commerce API Gateway",
    description="Main entry point for the e-commerce platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Instrument FastAPI with OpenTelemetry
# This automatically creates spans for all HTTP requests
FastAPIInstrumentor.instrument_app(app)

# Instrument httpx client for automatic trace propagation to downstream services
HTTPXClientInstrumentor().instrument()

# Expose default Prometheus metrics at /metrics
Instrumentator().instrument(app).expose(app, include_in_schema=False)


# No manual middleware needed!
# OpenTelemetry FastAPIInstrumentation automatically:
# 1. Creates a span for each request
# 2. Propagates W3C Trace Context headers
# 3. Makes trace_id and span_id available to logs


@app.get("/")
async def root():
    """Health check endpoint."""
    logger.info("Health check called")
    return {"service": "api_gateway", "status": "healthy", "version": "1.0.0"}


@app.get("/products")
async def get_products():
    """
    Get all products from the Product Service.


    """
    logger.info("Fetching products from Product Service")

    try:
        # Call Product Service
        # HTTPXClientInstrumentation automatically propagates trace context
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PRODUCT_SERVICE_URL}/products",
                timeout=5.0,
            )
            response.raise_for_status()

        products = response.json()
        logger.info(
            "Products retrieved successfully",
            extra={"product_count": len(products)},
        )

        return products

    except httpx.HTTPError as e:
        logger.error(
            "Failed to fetch products from Product Service",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=503, detail="Product Service unavailable"
        ) from e


@app.get("/products/{product_id}")
async def get_product(product_id: int):
    """Get a specific product by ID."""
    logger.info("Fetching product details", extra={"product_id": product_id})

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PRODUCT_SERVICE_URL}/products/{product_id}",
                timeout=5.0,
            )
            response.raise_for_status()

        product = response.json()
        logger.info(
            "Product retrieved successfully",
            extra={"product_id": product_id, "product_name": product.get("name")},
        )

        return product

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning("Product not found", extra={"product_id": product_id})
            raise HTTPException(status_code=404, detail="Product not found") from e
        raise


@app.post("/orders")
async def create_order(order_data: dict):
    """
    Create a new order.

    This demonstrates a complex multi-service flow:
    1. Validate product exists (call Product Service)
    2. Create order (call Order Service)
    3. All with automatic trace propagation

    """
    logger.info("Creating new order", extra={"order_data": order_data})

    try:
        # First, verify the product exists
        product_id = order_data.get("product_id")
        if not product_id:
            raise HTTPException(status_code=400, detail="product_id is required")

        async with httpx.AsyncClient() as client:
            # Check product exists
            logger.debug("Verifying product exists", extra={"product_id": product_id})
            product_response = await client.get(
                f"{PRODUCT_SERVICE_URL}/products/{product_id}",
                timeout=5.0,
            )
            product_response.raise_for_status()

            # Create order
            logger.debug("Calling Order Service to create order")
            order_response = await client.post(
                f"{ORDER_SERVICE_URL}/orders",
                json=order_data,
                timeout=5.0,
            )
            order_response.raise_for_status()

        order = order_response.json()
        logger.info(
            "Order created successfully",
            extra={"order_id": order.get("id"), "product_id": product_id},
        )

        return order

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.error("Product not found when creating order", extra={"product_id": product_id})
            raise HTTPException(status_code=404, detail="Product not found") from e
        logger.error("Failed to create order", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=503, detail="Order creation failed") from e


@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    """Get order details."""
    logger.info("Fetching order details", extra={"order_id": order_id})

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ORDER_SERVICE_URL}/orders/{order_id}",
                timeout=5.0,
            )
            response.raise_for_status()

        order = response.json()
        logger.info("Order retrieved successfully", extra={"order_id": order_id})

        return order

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning("Order not found", extra={"order_id": order_id})
            raise HTTPException(status_code=404, detail="Order not found") from e
        raise


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting API Gateway on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
