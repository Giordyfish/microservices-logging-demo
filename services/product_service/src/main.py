"""
Product Service for E-Commerce Platform

This service manages the product catalog.
It provides endpoints to list products and get product details.

"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from typing import List, Dict

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
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
SERVICE_NAME = "product_service"
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

# Initialize OpenTelemetry
resource = Resource.create({"service.name": SERVICE_NAME})
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)

otlp_exporter = OTLPSpanExporter(endpoint=f"{OTEL_ENDPOINT}/v1/traces")
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)

# Initialize logger
logger = setup_logging(SERVICE_NAME, console_level="DEBUG", enable_file_logging=True)

# In-memory product database (for demonstration purposes)
# In a real application, this would be a database
PRODUCTS_DB: List[Dict] = [
    {
        "id": 1,
        "name": "Laptop",
        "description": "High-performance laptop for professionals",
        "price": 1299.99,
        "stock": 15,
        "category": "Electronics",
    },
    {
        "id": 2,
        "name": "Wireless Mouse",
        "description": "Ergonomic wireless mouse with precision tracking",
        "price": 29.99,
        "stock": 50,
        "category": "Electronics",
    },
    {
        "id": 3,
        "name": "Mechanical Keyboard",
        "description": "RGB mechanical keyboard with Cherry MX switches",
        "price": 149.99,
        "stock": 25,
        "category": "Electronics",
    },
    {
        "id": 4,
        "name": "USB-C Hub",
        "description": "7-in-1 USB-C hub with HDMI and Ethernet",
        "price": 49.99,
        "stock": 40,
        "category": "Accessories",
    },
    {
        "id": 5,
        "name": "Monitor Stand",
        "description": "Adjustable monitor stand with cable management",
        "price": 39.99,
        "stock": 30,
        "category": "Accessories",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    # Startup
    logger.info(
        "Product Service starting up",
        extra={"product_count": len(PRODUCTS_DB), "otel_endpoint": OTEL_ENDPOINT},
    )
    yield
    # Shutdown
    logger.info("Product Service shutting down")
    tracer_provider.force_flush()


# Create FastAPI app
app = FastAPI(
    title="Product Service",
    description="Manages product catalog for the e-commerce platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

# Expose default Prometheus metrics at /metrics
Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.get("/")
async def root():
    """Health check endpoint."""
    logger.info("Health check called")
    return {"service": "product_service", "status": "healthy", "version": "1.0.0"}


@app.get("/products")
async def get_products(category: str = None):
    """
    Get all products, optionally filtered by category.

    Query Parameters:
        category: Optional category filter (e.g., "Electronics")

    """
    logger.info("Fetching products", extra={"category_filter": category})

    # Filter by category if provided
    if category:
        filtered_products = [p for p in PRODUCTS_DB if p["category"] == category]
        logger.info(
            "Products filtered by category",
            extra={
                "category": category,
                "result_count": len(filtered_products),
                "total_count": len(PRODUCTS_DB),
            },
        )
        return filtered_products

    logger.info(
        "Returning all products",
        extra={"product_count": len(PRODUCTS_DB)},
    )
    return PRODUCTS_DB


@app.get("/products/{product_id}")
async def get_product(product_id: int):
    """
    Get a specific product by ID.

    Path Parameters:
        product_id: The ID of the product to retrieve

    """
    logger.info("Fetching product by ID", extra={"product_id": product_id})

    # Search for product
    product = next((p for p in PRODUCTS_DB if p["id"] == product_id), None)

    if not product:
        logger.warning(
            "Product not found",
            extra={
                "product_id": product_id,
                "available_ids": [p["id"] for p in PRODUCTS_DB],
            },
        )
        raise HTTPException(status_code=404, detail="Product not found")

    logger.info(
        "Product found",
        extra={
            "product_id": product_id,
            "product_name": product["name"],
            "price": product["price"],
        },
    )
    return product


@app.put("/products/{product_id}/stock")
async def update_stock(product_id: int, quantity_change: int):
    """
    Update product stock (for demonstration purposes).

    This would be called by the Order Service when an order is placed.

    Path Parameters:
        product_id: The ID of the product
    Body:
        quantity_change: Amount to add/subtract from stock (negative to decrease)

    """
    logger.info(
        "Updating product stock",
        extra={"product_id": product_id, "quantity_change": quantity_change},
    )

    # Find product
    product = next((p for p in PRODUCTS_DB if p["id"] == product_id), None)

    if not product:
        logger.warning("Cannot update stock - product not found", extra={"product_id": product_id})
        raise HTTPException(status_code=404, detail="Product not found")

    # Store old stock for logging
    old_stock = product["stock"]

    # Update stock
    new_stock = old_stock + quantity_change

    if new_stock < 0:
        logger.error(
            "Insufficient stock",
            extra={
                "product_id": product_id,
                "current_stock": old_stock,
                "requested_change": quantity_change,
            },
        )
        raise HTTPException(status_code=400, detail="Insufficient stock")

    product["stock"] = new_stock

    logger.info(
        "Stock updated successfully",
        extra={
            "product_id": product_id,
            "product_name": product["name"],
            "old_stock": old_stock,
            "new_stock": new_stock,
            "change": quantity_change,
        },
    )

    return {
        "product_id": product_id,
        "old_stock": old_stock,
        "new_stock": new_stock,
        "message": "Stock updated successfully",
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Product Service on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_config=None)
