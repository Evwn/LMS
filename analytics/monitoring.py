import psutil
import time
from prometheus_client import Counter, Gauge, Histogram
from django.core.cache import cache
from django.db import connection
from django.conf import settings

# Define Prometheus metrics
REQUEST_COUNT = Counter('django_http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('django_http_request_duration_seconds', 'HTTP request latency')
ERROR_COUNT = Counter('django_http_errors_total', 'Total HTTP errors')
ACTIVE_USERS = Gauge('django_active_users', 'Number of active users')
CPU_USAGE = Gauge('django_cpu_usage', 'CPU usage percentage')
MEMORY_USAGE = Gauge('django_memory_usage', 'Memory usage percentage')
DISK_USAGE = Gauge('django_disk_usage', 'Disk usage percentage')
DB_CONNECTIONS = Gauge('django_db_connections', 'Number of database connections')

class SystemMonitor:
    def __init__(self):
        self.cache_key_prefix = 'system_metrics_'
        self.metrics_ttl = 300  # 5 minutes

    def get_system_metrics(self):
        """Get current system metrics"""
        # Update Prometheus metrics
        CPU_USAGE.set(psutil.cpu_percent())
        MEMORY_USAGE.set(psutil.virtual_memory().percent)
        DISK_USAGE.set(psutil.disk_usage('/').percent)
        DB_CONNECTIONS.set(len(connection.queries))

        # Calculate server load (average of CPU, memory, and disk usage)
        cpu_usage = CPU_USAGE._value.get()
        memory_usage = MEMORY_USAGE._value.get()
        disk_usage = DISK_USAGE._value.get()
        server_load = (cpu_usage + memory_usage + disk_usage) / 3

        return {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'response_time': self._get_average_response_time(),
            'error_rate': self._get_error_rate(),
            'active_requests': self._get_active_requests(),
            'database_connections': DB_CONNECTIONS._value.get(),
            'server_load': server_load,
        }

    def _get_average_response_time(self):
        """Calculate average response time from cache"""
        cache_key = f"{self.cache_key_prefix}response_times"
        response_times = cache.get(cache_key, [])
        if not response_times:
            return 0
        return sum(response_times) / len(response_times)

    def _get_error_rate(self):
        """Calculate error rate from cache"""
        cache_key = f"{self.cache_key_prefix}errors"
        errors = cache.get(cache_key, 0)
        total_requests = cache.get(f"{self.cache_key_prefix}total_requests", 0)
        if total_requests == 0:
            return 0
        return (errors / total_requests) * 100

    def _get_active_requests(self):
        """Get number of active requests"""
        return cache.get(f"{self.cache_key_prefix}active_requests", 0)

    def record_request(self, response_time, is_error=False, method=None, endpoint=None, status=None):
        """Record a new request"""
        # Update Prometheus metrics
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_LATENCY.observe(response_time)
        if is_error:
            ERROR_COUNT.inc()

        # Record response time
        cache_key = f"{self.cache_key_prefix}response_times"
        response_times = cache.get(cache_key, [])
        response_times.append(response_time)
        if len(response_times) > 100:  # Keep last 100 requests
            response_times.pop(0)
        cache.set(cache_key, response_times, self.metrics_ttl)

        # Record total requests
        total_key = f"{self.cache_key_prefix}total_requests"
        total = cache.get(total_key, 0) + 1
        cache.set(total_key, total, self.metrics_ttl)

        # Record errors if any
        if is_error:
            error_key = f"{self.cache_key_prefix}errors"
            errors = cache.get(error_key, 0) + 1
            cache.set(error_key, errors, self.metrics_ttl)

    def get_system_uptime(self):
        """Calculate system uptime percentage"""
        cache_key = f"{self.cache_key_prefix}uptime"
        uptime_data = cache.get(cache_key, {'total': 0, 'successful': 0})
        if uptime_data['total'] == 0:
            return 100
        return (uptime_data['successful'] / uptime_data['total']) * 100

    def record_uptime(self, is_successful=True):
        """Record system uptime"""
        cache_key = f"{self.cache_key_prefix}uptime"
        uptime_data = cache.get(cache_key, {'total': 0, 'successful': 0})
        uptime_data['total'] += 1
        if is_successful:
            uptime_data['successful'] += 1
        cache.set(cache_key, uptime_data, self.metrics_ttl)

    def get_user_activity_metrics(self):
        """Get user activity metrics"""
        return {
            'active_users': ACTIVE_USERS._value.get(),
            'new_users_today': cache.get(f"{self.cache_key_prefix}new_users_today", 0),
            'total_logins_today': cache.get(f"{self.cache_key_prefix}total_logins_today", 0),
        }

    def record_user_activity(self, is_login=False, is_new_user=False):
        """Record user activity"""
        if is_login:
            cache_key = f"{self.cache_key_prefix}total_logins_today"
            logins = cache.get(cache_key, 0) + 1
            cache.set(cache_key, logins, self.metrics_ttl)
        
        if is_new_user:
            cache_key = f"{self.cache_key_prefix}new_users_today"
            new_users = cache.get(cache_key, 0) + 1
            cache.set(cache_key, new_users, self.metrics_ttl)

    def get_resource_utilization(self):
        """Get resource utilization metrics"""
        return {
            'total_resources': cache.get(f"{self.cache_key_prefix}total_resources", 0),
            'resource_accesses': cache.get(f"{self.cache_key_prefix}resource_accesses", 0),
        }

    def record_resource_access(self):
        """Record resource access"""
        cache_key = f"{self.cache_key_prefix}resource_accesses"
        accesses = cache.get(cache_key, 0) + 1
        cache.set(cache_key, accesses, self.metrics_ttl)

# Create a singleton instance
system_monitor = SystemMonitor() 