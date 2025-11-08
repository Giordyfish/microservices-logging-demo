"""
Order Service for E-Commerce Platform

This service manages customer orders.
It creates and tracks orders for products.

"""
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from typing import List, Dict
from enum import Enum

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
import sys
from pathlib import Path

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
SERVICE_NAME = "order_service"
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


class OrderStatus(str, Enum):
    """Order status enumeration."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# In-memory order database (for demonstration purposes)
ORDERS_DB: List[Dict] = []
ORDER_ID_COUNTER = 1


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    # Startup
    logger.info("Order Service starting up", extra={"otel_endpoint": OTEL_ENDPOINT})
    yield
    # Shutdown
    logger.info("Order Service shutting down")
    tracer_provider.force_flush()


# Create FastAPI app
app = FastAPI(
    title="Order Service",
    description="Manages orders for the e-commerce platform",
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
    return {"service": "order_service", "status": "healthy", "version": "1.0.0"}


@app.post("/orders")
async def create_order(order_data: dict):
    """
    Create a new order.

    Expected body:
    {
        "product_id": 1,
        "quantity": 2,
        "customer_name": "John Doe",
        "customer_email": "john@example.com"
    }

    """
    global ORDER_ID_COUNTER

    logger.info(
        "Creating new order",
        extra={
            "product_id": order_data.get("product_id"),
            "quantity": order_data.get("quantity"),
            "customer_name": order_data.get("customer_name"),
        },
    )

    # Validate required fields
    required_fields = ["product_id", "quantity", "customer_name", "customer_email"]
    for field in required_fields:
        if field not in order_data:
            logger.warning(
                "Order creation failed - missing required field",
                extra={"missing_field": field, "provided_data": list(order_data.keys())},
            )
            raise HTTPException(
                status_code=400, detail=f"Missing required field: {field}"
            )

    # Validate quantity
    quantity = order_data["quantity"]
    if quantity <= 0:
        logger.warning(
            "Order creation failed - invalid quantity",
            extra={"quantity": quantity},
        )
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    # Create order
    order = {
        "id": ORDER_ID_COUNTER,
        "product_id": order_data["product_id"],
        "quantity": quantity,
        "customer_name": order_data["customer_name"],
        "customer_email": order_data["customer_email"],
        "status": OrderStatus.PENDING,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

    # Calculate total (in real app, would fetch product price)
    # For demo, using placeholder price
    order["total_price"] = quantity * 99.99

    ORDERS_DB.append(order)
    ORDER_ID_COUNTER += 1

    logger.info(
        "Order created successfully",
        extra={
            "order_id": order["id"],
            "product_id": order["product_id"],
            "quantity": quantity,
            "customer_name": order["customer_name"],
            "total_price": order["total_price"],
            "status": order["status"],
        },
    )

    return order


@app.get("/orders")
async def get_orders(customer_email: str = None):
    """
    Get all orders, optionally filtered by customer email.

    Query Parameters:
        customer_email: Optional filter by customer email

    """
    logger.info(
        "Fetching orders",
        extra={"customer_email_filter": customer_email},
    )

    if customer_email:
        filtered_orders = [
            o for o in ORDERS_DB if o["customer_email"] == customer_email
        ]
        logger.info(
            "Orders filtered by customer",
            extra={
                "customer_email": customer_email,
                "result_count": len(filtered_orders),
                "total_count": len(ORDERS_DB),
            },
        )
        return filtered_orders

    logger.info(
        "Returning all orders",
        extra={"order_count": len(ORDERS_DB)},
    )
    return ORDERS_DB


@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    """
    Get a specific order by ID.

    """
    logger.info("Fetching order by ID", extra={"order_id": order_id})

    order = next((o for o in ORDERS_DB if o["id"] == order_id), None)

    if not order:
        logger.warning(
            "Order not found",
            extra={
                "order_id": order_id,
                "available_order_ids": [o["id"] for o in ORDERS_DB],
            },
        )
        raise HTTPException(status_code=404, detail="Order not found")

    logger.info(
        "Order found",
        extra={
            "order_id": order_id,
            "status": order["status"],
            "customer_name": order["customer_name"],
        },
    )
    return order


@app.patch("/orders/{order_id}/status")
async def update_order_status(order_id: int, status_data: dict):
    """
    Update order status.

    Expected body:
    {
        "status": "confirmed"  // or "shipped", "delivered", "cancelled"
    }

    """
    logger.info(
        "Updating order status",
        extra={
            "order_id": order_id,
            "new_status": status_data.get("status"),
        },
    )

    # Find order
    order = next((o for o in ORDERS_DB if o["id"] == order_id), None)

    if not order:
        logger.warning("Cannot update status - order not found", extra={"order_id": order_id})
        raise HTTPException(status_code=404, detail="Order not found")

    # Validate status
    new_status = status_data.get("status")
    try:
        OrderStatus(new_status)
    except ValueError:
        logger.warning(
            "Invalid order status",
            extra={
                "provided_status": new_status,
                "valid_statuses": [s.value for s in OrderStatus],
            },
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {[s.value for s in OrderStatus]}",
        )

    # Store old status for logging
    old_status = order["status"]

    # Update status
    order["status"] = new_status
    order["updated_at"] = datetime.now().isoformat()

    logger.info(
        "Order status updated successfully",
        extra={
            "order_id": order_id,
            "old_status": old_status,
            "new_status": new_status,
            "customer_name": order["customer_name"],
        },
    )

    return order


@app.delete("/orders/{order_id}")
async def cancel_order(order_id: int):
    """
    Cancel an order (soft delete by setting status to cancelled).

    """
    logger.info("Cancelling order", extra={"order_id": order_id})

    order = next((o for o in ORDERS_DB if o["id"] == order_id), None)

    if not order:
        logger.warning("Cannot cancel - order not found", extra={"order_id": order_id})
        raise HTTPException(status_code=404, detail="Order not found")

    # Check if already cancelled
    if order["status"] == OrderStatus.CANCELLED:
        logger.warning(
            "Order already cancelled",
            extra={"order_id": order_id},
        )
        raise HTTPException(status_code=400, detail="Order already cancelled")

    old_status = order["status"]
    order["status"] = OrderStatus.CANCELLED
    order["updated_at"] = datetime.now().isoformat()

    logger.info(
        "Order cancelled successfully",
        extra={
            "order_id": order_id,
            "previous_status": old_status,
            "customer_name": order["customer_name"],
            "customer_email": order["customer_email"],
        },
    )

    return {"message": "Order cancelled successfully", "order": order}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Order Service on port 8002")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_config=None)
