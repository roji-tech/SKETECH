from __future__ import annotations
import uuid
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest
from main.tenancy.threadlocals import set_current_request

class RequestIDMiddleware(MiddlewareMixin):
    """Attach a stable request id; helpful for audit trails/log correlation."""
    header = "HTTP_X_REQUEST_ID"

    def process_request(self, request: HttpRequest):
        rid = request.META.get(self.header) or uuid.uuid4().hex
        request.request_id = rid
        set_current_request(request)
