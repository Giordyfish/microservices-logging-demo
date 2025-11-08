"""
Custom logging filters for adding OpenTelemetry trace context to log records.

This automatically injects trace_id and span_id from OpenTelemetry into every log,
enabling correlation between logs and distributed traces.
"""

import logging
from .tracing import get_trace_id, get_span_id


class OTelTraceFilter(logging.Filter):
    """
    Logging filter that adds OpenTelemetry trace context to log records.

    This filter automatically extracts trace_id and span_id from the current
    OpenTelemetry context and adds them to every log record. This enables:

    1. Searching logs by trace_id in Loki
    2. Jumping from logs to traces in Grafana
    3. Correlating logs across multiple services in a single request

    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add trace_id and span_id to the log record if available.

        Args:
            record: The log record to filter.

        Returns:
            Always True (we don't filter out records, just add data).
        """
        # Extract trace context from OpenTelemetry
        trace_id = get_trace_id()
        span_id = get_span_id()

        # Add to log record as extra fields
        if trace_id:
            record.trace_id = trace_id
        if span_id:
            record.span_id = span_id

        return True
