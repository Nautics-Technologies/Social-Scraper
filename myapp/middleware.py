# myapp/middleware.py
import logging
from django.core.exceptions import MiddlewareNotUsed

class IgnoreClientAbortMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except (BrokenPipeError, ConnectionResetError) as e:
            logging.warning(f"Client aborted request: {e}")
            return MiddlewareNotUsed()
