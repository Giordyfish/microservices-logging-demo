"""
OpenTelemetry trace context utilities for distributed tracing.
Extracts trace_id and span_id from the current OpenTelemetry context.

This replaces manual correlation ID tracking with industry-standard W3C Trace Context.

Note: OpenTelemetry imports are lazy (inside functions) to allow this module
to be imported even if OpenTelemetry is not installed yet.
"""

from typing import Optional


def get_trace_id() -> Optional[str]:
    """
    Get the current trace ID from OpenTelemetry context.

    The trace ID uniquely identifies a request as it flows through multiple services.
    This is automatically generated and propagated by OpenTelemetry instrumentation.

    Returns:
        Hex string representation of the trace ID, or None if no active span.

    Example:
        >>> get_trace_id()
        '4bf92f3577b34da6a3ce929d0e0e4736'
    """
    try:
        # Lazy import to avoid requiring opentelemetry at module import time
        from opentelemetry import trace

        span = trace.get_current_span()
        if span and span.get_span_context().trace_id != 0:
            # Convert trace_id (128-bit int) to 32-char hex string
            return format(span.get_span_context().trace_id, "032x")
    except ImportError:
        # OpenTelemetry not installed, return None
        pass
    return None


def get_span_id() -> Optional[str]:
    """
    Get the current span ID from OpenTelemetry context.

    The span ID identifies a specific operation within a trace.
    Each service call creates a new span with its own span_id.

    Returns:
        Hex string representation of the span ID, or None if no active span.

    Example:
        >>> get_span_id()
        '00f067aa0ba902b7'
    """
    try:
        # Lazy import to avoid requiring opentelemetry at module import time
        from opentelemetry import trace

        span = trace.get_current_span()
        if span and span.get_span_context().span_id != 0:
            # Convert span_id (64-bit int) to 16-char hex string
            return format(span.get_span_context().span_id, "016x")
    except ImportError:
        # OpenTelemetry not installed, return None
        pass
    return None


def get_trace_context() -> dict:
    """
    Get both trace_id and span_id as a dictionary.

    This is useful for adding trace context to logs or external calls.

    Returns:
        Dictionary with trace_id and span_id keys.

    Example:
        >>> get_trace_context()
        {'trace_id': '4bf92f3577b34da6a3ce929d0e0e4736', 'span_id': '00f067aa0ba902b7'}
    """
    return {
        "trace_id": get_trace_id(),
        "span_id": get_span_id(),
    }
