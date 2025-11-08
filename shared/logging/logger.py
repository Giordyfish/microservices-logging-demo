"""
Main logging setup and configuration.
Provides structured logging with JSON output and colored console.
"""

import logging
import os
import sys
from typing import Dict, Optional

from .formatters import JsonLineFormatter, ColoredConsoleFormatter
from .filters import OTelTraceFilter


_OTLP_HANDLERS: Dict[str, logging.Handler] = {}


def _get_otlp_logging_handler(
    service_name: str, otlp_endpoint: str
) -> Optional[logging.Handler]:
    """
    Lazily build a LoggingHandler that forwards Python logs to the OTLP collector.
    """
    if service_name in _OTLP_HANDLERS:
        return _OTLP_HANDLERS[service_name]

    try:
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.resources import Resource
    except ImportError:
        return None

    endpoint = otlp_endpoint.rstrip("/")
    exporter = OTLPLogExporter(endpoint=f"{endpoint}/v1/logs")
    provider = LoggerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

    handler = LoggingHandler(level=logging.NOTSET, logger_provider=provider)
    _OTLP_HANDLERS[service_name] = handler
    return handler


def setup_logging(
    service_name: str,
    console_level: str = "DEBUG",
    file_level: str = "INFO",
    log_dir: str = "./logs",
    enable_file_logging: bool = True,
    enable_otlp_logging: bool = True,
    otlp_endpoint: Optional[str] = None,
) -> logging.Logger:
    """
    Set up logging for a microservice.

    This configures:
    - Colored console output for development
    - JSON file output for log aggregation
    - OpenTelemetry trace context (trace_id and span_id) in all logs

    Args:
        service_name: Name of the service (e.g., "api_gateway")
        console_level: Log level for console output (default: DEBUG)
        file_level: Log level for file output (default: INFO)
        log_dir: Directory to store log files (default: ./logs)
        enable_file_logging: Whether to enable file logging (default: True)

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logging("api_gateway")
        >>> logger.info("Service started", extra={"port": 8000})
    """
    # Create log directory if needed
    if enable_file_logging and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Get or create logger
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()

    # --- Console Handler (Colored) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, console_level.upper(), logging.DEBUG))
    console_formatter = ColoredConsoleFormatter(datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(console_formatter)

    # --- File Handler (JSON) ---
    file_handler = None
    if enable_file_logging:
        log_file = os.path.join(log_dir, f"{service_name}.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(getattr(logging, file_level.upper(), logging.INFO))
        json_formatter = JsonLineFormatter(datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(json_formatter)

    # --- Add OpenTelemetry Trace Filter ---
    # This automatically injects trace_id and span_id into every log
    otel_filter = OTelTraceFilter()
    console_handler.addFilter(otel_filter)
    if file_handler:
        file_handler.addFilter(otel_filter)

    # --- Attach Handlers ---
    logger.addHandler(console_handler)
    if file_handler:
        logger.addHandler(file_handler)

    # --- OTLP Handler (sends logs to collector for Loki) ---
    if enable_otlp_logging:
        effective_endpoint = otlp_endpoint or os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318"
        )
        if effective_endpoint:
            otlp_handler = _get_otlp_logging_handler(service_name, effective_endpoint)
            if otlp_handler:
                otlp_handler.addFilter(otel_filter)
                logger.addHandler(otlp_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(service_name: str) -> logging.Logger:
    """
    Get an existing logger by service name.

    If the logger doesn't exist, it will be created with default settings.

    Args:
        service_name: Name of the service

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger("api_gateway")
        >>> logger.info("Processing request")
    """
    logger = logging.getLogger(service_name)
    if not logger.handlers:
        # Logger not set up yet, initialize it with defaults
        return setup_logging(service_name)
    return logger
