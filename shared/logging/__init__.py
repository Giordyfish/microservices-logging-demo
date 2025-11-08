"""
Shared logging utilities for microservices demo.
Based on haven-v2 logging patterns with full OpenTelemetry integration.

Automatically injects trace_id and span_id from OpenTelemetry into all logs.
"""

from .logger import get_logger, setup_logging
from .tracing import (
    get_trace_id,
    get_span_id,
    get_trace_context,
)

__all__ = [
    "get_logger",
    "setup_logging",
    "get_trace_id",
    "get_span_id",
    "get_trace_context",
]
