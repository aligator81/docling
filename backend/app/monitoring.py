import logging
import json
import time
import psutil
import os
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Callable
from contextlib import contextmanager

# Configure structured logging
class StructuredLogger:
    def __init__(self, name: str = "docling"):
        self.logger = logging.getLogger(name)
        self._setup_logging()

    def _setup_logging(self):
        """Configure structured JSON logging"""
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Create console handler with JSON formatting
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "function": "%(funcName)s", "line": "%(lineno)d", "message": "%(message)s"}'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False

    def log_api_request(self, method: str, endpoint: str, status_code: int, duration: float, client_ip: str = None):
        """Log API request details"""
        log_data = {
            "event_type": "api_request",
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2),
            "client_ip": client_ip,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.info(json.dumps(log_data))

    def log_document_event(self, event_type: str, document_id: int, user_id: int = None, **kwargs):
        """Log document-related events"""
        log_data = {
            "event_type": event_type,
            "document_id": document_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.info(json.dumps(log_data))

    def log_error(self, error_type: str, error_message: str, **kwargs):
        """Log error events"""
        log_data = {
            "event_type": "error",
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.error(json.dumps(log_data))

    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        log_data = {
            "event_type": "performance",
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.logger.info(json.dumps(log_data))

# Global logger instance
structured_logger = StructuredLogger()

class QueryMonitor:
    def __init__(self):
        self.slow_query_threshold = 1.0  # seconds

    def monitor_query(self, query_func: Callable) -> Callable:
        """Decorator to monitor database query performance"""
        @wraps(query_func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = query_func(*args, **kwargs)
                execution_time = time.time() - start_time

                if execution_time > self.slow_query_threshold:
                    structured_logger.log_performance(
                        "slow_database_query",
                        execution_time,
                        query_function=query_func.__name__,
                        threshold_seconds=self.slow_query_threshold
                    )

                return result
            except Exception as e:
                execution_time = time.time() - start_time
                structured_logger.log_error(
                    "database_query_error",
                    str(e),
                    query_function=query_func.__name__,
                    execution_time=execution_time
                )
                raise

        return wrapper

    @contextmanager
    def monitor_query_context(self, query_name: str):
        """Context manager for monitoring query performance"""
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            if execution_time > self.slow_query_threshold:
                structured_logger.log_performance(
                    "slow_database_query",
                    execution_time,
                    query_name=query_name,
                    threshold_seconds=self.slow_query_threshold
                )

# Global query monitor instance
query_monitor = QueryMonitor()

class SystemMonitor:
    def __init__(self):
        self.process = psutil.Process()

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            disk_usage = psutil.disk_usage('/')

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used / 1024 / 1024,
                "disk_percent": disk_usage.percent,
                "disk_used_gb": disk_usage.used / 1024 / 1024 / 1024,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            structured_logger.log_error("system_monitor_error", str(e))
            return {}

    def get_database_connections(self) -> Dict[str, Any]:
        """Get database connection pool metrics"""
        try:
            # This would require access to SQLAlchemy engine pool stats
            # For now, return basic information
            return {
                "pool_size": getattr(self, '_pool_size', 'unknown'),
                "active_connections": getattr(self, '_active_connections', 'unknown'),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            structured_logger.log_error("database_monitor_error", str(e))
            return {}

# Global system monitor instance
system_monitor = SystemMonitor()

def log_api_middleware(app):
    """Middleware function to log API requests"""
    @wraps(app)
    async def wrapper(request, call_next):
        start_time = time.time()

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Log the API request
            structured_logger.log_api_request(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                duration=duration,
                client_ip=client_ip
            )

            return response

        except Exception as e:
            duration = time.time() - start_time
            structured_logger.log_error(
                "api_request_error",
                str(e),
                method=request.method,
                endpoint=request.url.path,
                client_ip=client_ip,
                duration=duration
            )
            raise

    return wrapper

# Performance monitoring decorator
def monitor_performance(operation_name: str):
    """Decorator to monitor function performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                structured_logger.log_performance(
                    operation_name,
                    duration,
                    function_name=func.__name__
                )

                return result
            except Exception as e:
                duration = time.time() - start_time
                structured_logger.log_error(
                    "performance_monitor_error",
                    str(e),
                    operation_name=operation_name,
                    function_name=func.__name__,
                    duration=duration
                )
                raise

        return wrapper
    return decorator

# Health check function
def health_check() -> Dict[str, Any]:
    """Perform application health check"""
    try:
        # System health
        system_metrics = system_monitor.get_system_metrics()

        # Database health (basic check)
        from .database import engine
        try:
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        # Check if uploads directory exists
        uploads_dir = "data/uploads"
        uploads_exists = os.path.exists(uploads_dir)

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "system": system_metrics,
            "database": db_status,
            "uploads_directory": "exists" if uploads_exists else "missing"
        }

    except Exception as e:
        structured_logger.log_error("health_check_error", str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }