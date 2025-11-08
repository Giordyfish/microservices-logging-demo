"""
Custom log formatters for JSON and colored console output.
"""

import json
import logging
from typing import Any, Dict


class JsonLineFormatter(logging.Formatter):
    """
    Outputs every log record as one JSON line.

    This is ideal for log aggregation systems like Loki, as each line
    is a complete, parseable JSON object.

    Example output:
    {
      "time": "2025-01-08 10:30:45",
      "level": "INFO",
      "logger": "api_gateway",
      "message": "Request received",
      "correlation_id": "abc-123",
      "trace_id": "xyz-789"
    }
    """

    # Standard LogRecord attributes that we don't want to include as extras
    _STD_ATTRS = set(vars(logging.LogRecord("", 0, "", 0, "", (), None)).keys())

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON line.

        Args:
            record: The log record to format.

        Returns:
            A JSON string representing the log record.
        """
        # Handle dict/list messages differently
        if isinstance(record.msg, (dict, list)):
            msg_val: Any = record.msg
        else:
            msg_val = record.getMessage()

        # Build base payload
        payload: Dict[str, Any] = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": msg_val,
        }

        # Add all extras (including correlation_id, trace_id, span_id if present)
        for k, v in record.__dict__.items():
            if k in self._STD_ATTRS or k in ("msg", "args"):
                continue
            try:
                # Test if value is JSON serializable
                json.dumps(v)
                payload[k] = v
            except Exception:
                # If not, convert to string
                payload[k] = str(v)

        # Add exception info if any
        if record.exc_info:
            try:
                payload["err"] = self.formatException(record.exc_info)
            except Exception:
                import traceback

                payload["err"] = "".join(traceback.format_exception(*record.exc_info))

        return json.dumps(payload, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """
    Colored console formatter that displays logs in an easy-to-read format.

    Main line: timestamp | level | logger | message
    Extra fields on separate lines as "key": value

    This makes it easy to see what's happening at a glance during development.
    """

    _STD_ATTRS = set(vars(logging.LogRecord("", 0, "", 0, "", (), None)).keys())

    # ANSI color codes for different log levels
    COLORS = {
        "DEBUG": "\033[36m",  # cyan
        "INFO": "\033[32m",  # green
        "WARNING": "\033[33m",  # yellow
        "ERROR": "\033[31m",  # red
        "CRITICAL": "\033[31;47m",  # red text on white background
    }
    CYAN = "\033[36m"
    PURPLE = "\033[35m"
    THIN_WHITE = "\033[37m"
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with colors.

        Args:
            record: The log record to format.

        Returns:
            A colored string representing the log record.
        """
        # Get message
        if isinstance(record.msg, (dict, list)):
            msg_val = json.dumps(record.msg, ensure_ascii=False)
        else:
            msg_val = record.getMessage()

        # Format timestamp
        timestamp = self.formatTime(record, self.datefmt)

        # Get colors
        level_color = self.COLORS.get(record.levelname, "")

        # Main log line with color coding
        main_line = (
            f"{self.CYAN}{timestamp} {level_color}│{self.RESET} "
            f"{level_color}{record.levelname:<8}{self.RESET} {level_color}│{self.RESET} "
            f"{self.PURPLE}{record.name:<15}{level_color}│{self.RESET} "
            f"{msg_val} "
            f"{self.RESET}"
        )

        lines = [main_line]

        # Collect extra fields
        extra_fields = []
        for k, v in record.__dict__.items():
            if k in self._STD_ATTRS or k in ("msg", "args"):
                continue
            extra_fields.append((k, v))

        # Format extra fields with tree-like connectors
        for i, (k, v) in enumerate(extra_fields):
            try:
                if isinstance(v, (dict, list)):
                    value_str = json.dumps(v, ensure_ascii=False)
                else:
                    value_str = str(v)

                # Use └─ for last item, ├─ for others
                connector = "└─" if i == len(extra_fields) - 1 else "├─"
                lines.append(
                    f'    {self.THIN_WHITE}{connector} "{k}": {value_str}{self.RESET}'
                )
            except Exception:
                connector = "└─" if i == len(extra_fields) - 1 else "├─"
                lines.append(
                    f'    {self.THIN_WHITE}{connector} "{k}": {str(v)}{self.RESET}'
                )

        # Add exception info if any
        if record.exc_info:
            try:
                exc_text = self.formatException(record.exc_info)
                lines.append(f"{self.COLORS['ERROR']}{exc_text}{self.RESET}")
            except Exception:
                import traceback

                exc_text = "".join(traceback.format_exception(*record.exc_info))
                lines.append(f"{self.COLORS['ERROR']}{exc_text}{self.RESET}")

        return "\n".join(lines)
