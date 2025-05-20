import time
from .monitoring import system_monitor

class MonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start timing the request
        start_time = time.time()
        
        # Process the request
        response = self.get_response(request)
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Record the request metrics
        system_monitor.record_request(
            response_time=response_time,
            is_error=response.status_code >= 400,
            method=request.method,
            endpoint=request.path,
            status=response.status_code
        )
        
        # Record system uptime
        system_monitor.record_uptime(response.status_code < 500)
        
        return response 