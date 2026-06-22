"""
Phase 2 Logging & Monitoring System.

Structured logging with JSON output for production and colored console
output for development. Includes request metrics tracking and a
periodic stats reporter.

Features:
- Structured JSON logging (production) / colored console (dev)
- Per-module loggers with consistent formatting
- Request metrics: counts, latencies, error rates
- Periodic stats reporting to admin
- Bot event tracking (new users, scans, premium purchases)
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field
from collections import defaultdict

# ─── CONFIG ───────────────────────────────────────────────────────────────────

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "console")  # "console" or "json"
LOG_FILE = os.getenv("LOG_FILE", "")  # Optional file path for log output
METRICS_REPORT_INTERVAL = int(os.getenv("METRICS_REPORT_INTERVAL", "3600"))  # seconds


# ─── JSON FORMATTER ───────────────────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    """Outputs logs as single-line JSON objects for structured log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        # Add extra fields
        for key in ("user_id", "chat_id", "url", "api_name", "duration_ms", "event"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry, ensure_ascii=False)


# ─── COLORED CONSOLE FORMATTER ────────────────────────────────────────────────

class ColoredFormatter(logging.Formatter):
    """Human-readable colored output for development."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Build extra context string
        extras = []
        for key in ("user_id", "chat_id", "url", "api_name", "duration_ms", "event"):
            if hasattr(record, key):
                extras.append(f"{key}={getattr(record, key)}")
        extra_str = f" [{', '.join(extras)}]" if extras else ""

        return (
            f"{color}{timestamp} [{record.levelname:>7}]{self.RESET} "
            f"{record.name}: {record.getMessage()}{extra_str}"
        )


# ─── LOGGING SETUP ────────────────────────────────────────────────────────────

def setup_logging():
    """Configure the root logger and all safelink.* loggers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if LOG_FORMAT == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter())
    console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    root_logger.addHandler(console_handler)

    # Optional file handler
    if LOG_FILE:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(JSONFormatter())  # Always JSON for files
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    logger = logging.getLogger("safelink")
    logger.info("Logging initialized (level=%s, format=%s)", LOG_LEVEL, LOG_FORMAT)


def get_logger(name: str) -> logging.Logger:
    """Get a namespaced logger under 'safelink.*'."""
    return logging.getLogger(f"safelink.{name}")


# ─── METRICS TRACKER ──────────────────────────────────────────────────────────

@dataclass
class MetricPoint:
    """A single metric data point."""
    count: int = 0
    total_duration_ms: float = 0.0
    errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None


class MetricsTracker:
    """
    Tracks bot-wide metrics for monitoring and admin reporting.
    
    Usage:
        metrics = MetricsTracker()
        
        # Track a URL scan
        metrics.record_scan("virustotal", duration_ms=230, success=True)
        
        # Track a new user
        metrics.record_event("new_user")
        
        # Get report
        report = metrics.get_report()
    """

    def __init__(self):
        self._scans: dict[str, MetricPoint] = defaultdict(MetricPoint)
        self._events: dict[str, int] = defaultdict(int)
        self._hourly_scans: dict[str, int] = defaultdict(int)
        self._start_time = datetime.now()
        self._lock = asyncio.Lock()

    async def record_scan(self, api_name: str, duration_ms: float = 0, success: bool = True, error: str = None):
        """Record an API scan call."""
        async with self._lock:
            metric = self._scans[api_name]
            metric.count += 1
            metric.total_duration_ms += duration_ms
            if not success:
                metric.errors += 1
                metric.last_error = error
                metric.last_error_time = datetime.now()

            # Track hourly
            hour_key = f"{api_name}:{datetime.now().strftime('%Y-%m-%d-%H')}"
            self._hourly_scans[hour_key] += 1

    async def record_event(self, event_name: str, count: int = 1):
        """Record a bot event (new_user, premium_purchase, referral, etc.)."""
        async with self._lock:
            self._events[event_name] += count

    async def get_report(self) -> dict:
        """Generate a metrics report."""
        async with self._lock:
            uptime = datetime.now() - self._start_time
            uptime_str = str(uptime).split(".")[0]  # Remove microseconds

            scan_stats = {}
            for api_name, metric in self._scans.items():
                avg_ms = metric.total_duration_ms / metric.count if metric.count > 0 else 0
                error_rate = (metric.errors / metric.count * 100) if metric.count > 0 else 0
                scan_stats[api_name] = {
                    "total_calls": metric.count,
                    "avg_latency_ms": round(avg_ms, 1),
                    "errors": metric.errors,
                    "error_rate_percent": round(error_rate, 1),
                    "last_error": metric.last_error,
                }

            return {
                "uptime": uptime_str,
                "total_scans": sum(m.count for m in self._scans.values()),
                "total_errors": sum(m.errors for m in self._scans.values()),
                "scan_stats": scan_stats,
                "events": dict(self._events),
            }

    async def get_formatted_report(self) -> str:
        """Generate a Markdown-formatted report for admin messages."""
        report = await self.get_report()

        text = "📊 *SafeLink Metrics Report*\n\n"
        text += f"⏱ Uptime: `{report['uptime']}`\n"
        text += f"🔍 Total Scans: `{report['total_scans']}`\n"
        text += f"❌ Total Errors: `{report['total_errors']}`\n\n"

        text += "📡 *API Stats:*\n"
        for api_name, stats in report["scan_stats"].items():
            status_emoji = "✅" if stats["error_rate_percent"] < 5 else "⚠️" if stats["error_rate_percent"] < 20 else "🔴"
            text += (
                f"{status_emoji} `{api_name}`: "
                f"{stats['total_calls']} calls, "
                f"~{stats['avg_latency_ms']}ms avg, "
                f"{stats['error_rate_percent']}% errors\n"
            )

        if report["events"]:
            text += "\n📈 *Events:*\n"
            for event, count in report["events"].items():
                text += f"• {event}: `{count}`\n"

        return text

    async def reset(self):
        """Reset all metrics (e.g., after reporting)."""
        async with self._lock:
            self._scans.clear()
            self._events.clear()
            self._hourly_scans.clear()
            self._start_time = datetime.now()


# ─── HEALTH CHECK ─────────────────────────────────────────────────────────────

class HealthChecker:
    """
    Simple health check that tracks component status.
    Useful for monitoring endpoints or periodic status reports.
    """

    def __init__(self):
        self._components: dict[str, dict] = {}

    def register(self, name: str):
        """Register a component to track."""
        self._components[name] = {
            "status": "unknown",
            "last_check": None,
            "message": "",
        }

    def update(self, name: str, healthy: bool, message: str = ""):
        """Update component health status."""
        self._components[name] = {
            "status": "healthy" if healthy else "unhealthy",
            "last_check": datetime.now().isoformat(),
            "message": message,
        }

    def is_healthy(self) -> bool:
        """Returns True if all registered components are healthy."""
        if not self._components:
            return True
        return all(c["status"] == "healthy" for c in self._components.values())

    def get_status(self) -> dict:
        """Get full health status."""
        return {
            "overall": "healthy" if self.is_healthy() else "degraded",
            "components": self._components,
            "checked_at": datetime.now().isoformat(),
        }

    def get_formatted_status(self) -> str:
        """Markdown-formatted health status."""
        status = self.get_status()
        emoji = "✅" if status["overall"] == "healthy" else "⚠️"
        text = f"{emoji} *System Health: {status['overall'].upper()}*\n\n"

        for name, info in status["components"].items():
            comp_emoji = "✅" if info["status"] == "healthy" else "❌"
            text += f"{comp_emoji} {name}: {info['status']}"
            if info["message"]:
                text += f" — {info['message']}"
            text += "\n"

        return text


# ─── GLOBAL INSTANCES ─────────────────────────────────────────────────────────

metrics = MetricsTracker()
health = HealthChecker()

# Register default components
health.register("database")
health.register("cache")
health.register("virustotal")
health.register("google_safe_browsing")
health.register("alienvault")
health.register("urlscan")
