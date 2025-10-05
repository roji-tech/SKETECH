# ==============================================
# File: main/tenancy/middlewares.py
# Purpose: Unified tenant resolution middleware
# ==============================================
from __future__ import annotations
from typing import Optional
import time
import logging
import os
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import ContentType
from django.db.models import Q
from django.http.response import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest, HttpResponse, JsonResponse, Http404
from django.db import connection
from django.utils.timezone import datetime

from main.tenancy.threadlocals import get_current_school, set_current_request, set_current_school
from main.models import School, User
from main.tenancy.utils import extract_subdomain
from main.models import AuditLog


# Configure audit logger
audit_logger = logging.getLogger('audit')

if not audit_logger.handlers:
    from logging.handlers import RotatingFileHandler

    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    audit_log_file = os.path.join(log_dir, 'audit.log')
    file_handler = RotatingFileHandler(
        audit_log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5
    )

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - School:%(school_id)s - User:%(user_id)s:%(user_email)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    audit_logger.addHandler(file_handler)
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False


class AuditLogFilter(logging.Filter):
    """Filter to add contextual information to audit log records."""

    def filter(self, record):
        from main.tenancy.threadlocals import get_current_school

        school = get_current_school()
        user = getattr(record, 'user', None) or getattr(
            record, 'request', None) and getattr(record.request, 'user', None)

        record.school_id = str(school.id) if school else 'none'
        record.user_id = str(user.id) if user and hasattr(
            user, 'id') else 'anonymous'
        record.user_email = getattr(user, 'email', 'anonymous')

        return True


# Add the filter to the audit logger
audit_logger.addFilter(AuditLogFilter())


class TenantResolver:
    """Utility class to handle tenant resolution logic."""

    @staticmethod
    def extract_subdomain_from_host(host: str) -> Optional[str]:
        """Extract subdomain from host, handling various scenarios."""
        if not host:
            return None

        # Remove port if present
        host = host.split(':')[0].lower().strip()
        domain_parts = host.split('.')

        # Handle localhost/development scenarios
        if len(domain_parts) <= 2 or domain_parts[-1] in ['localhost', 'local']:
            subdomain = domain_parts[0]
            return subdomain if subdomain not in ['www', 'app', 'api', 'admin'] else None

        # Handle production domains (subdomain.domain.tld)
        if len(domain_parts) >= 3:
            subdomain = domain_parts[0]
            return subdomain if subdomain not in ['www', 'app', 'api', 'admin'] else None

        return None

    @staticmethod
    def extract_from_base_domain(host: str, base_domain: str = None) -> Optional[str]:
        """Extract subdomain using BASE_DOMAIN configuration."""
        if not base_domain:
            base_domain = getattr(settings, 'BASE_DOMAIN', None) or getattr(
                settings, 'TENANCY_BASE_DOMAIN', None)

        if not base_domain:
            return None

        host = host.split(":", 1)[0].strip().lower()

        if host == base_domain or host.endswith("." + base_domain):
            subdomain = host[: -len(base_domain)].rstrip(".")
            return subdomain if subdomain and subdomain not in ['www', 'app', 'api', 'admin'] else None

        return None

    @staticmethod
    def lookup_school(identifier: str) -> Optional[School]:
        """Look up school by code, subdomain, or short_code."""
        if not identifier:
            return None

        return School.objects.filter(
            Q(code__iexact=identifier) |
            Q(subdomain__iexact=identifier),
            is_active=True
        ).first()


class UnifiedTenantMiddleware(MiddlewareMixin):
    """
    Unified middleware for tenant resolution and context management.

    Resolution order:
    1. Subdomain (subdomain.domain.com or using BASE_DOMAIN)
    2. HTTP_X_SCHOOL header (for API/testing)

    Supports: code or subdomain fields for school lookup.
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)
        # Add registration and auth endpoints to skip paths
        self.SKIP_PATHS = [
            '/static/',
            '/media/',
            '/health/',
            '/favicon.ico',
            '/api/v1/auth/users/',  # Allow all auth endpoints
            '/auth/',         # For backward compatibility
        ]
        self.DO_NOT_SKIP_PATHS = [
            '/api/v1/auth/login',  # Allow all auth endpoints
        ]
        self.SYSTEM_SUBDOMAINS = ['www', 'app', 'api', 'admin']

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Process incoming request to resolve tenant context."""
        # Initialize request context
        request._request_start_time = time.time()
        request.school = None
        request.school_code = None

        # Skip tenant processing for certain paths
        if self._should_skip_processing(request):
            print("\n\n\n\n\nSkipping tenant processing for certain paths.\n\n\n\n\n")
            return None

        print("\n\n\n\n\nNot Skipping, Processing tenant processing for certain paths.\n\n")
        try:
            school = self._resolve_school(request)
            print("\n\nSchool: ", school)

            if school:
                # Set school context
                # request.school = school
                # request.school_code = school.code
                request.school_id = school.id
                setattr(request, "school_id", school.id)
                set_current_school(school.id)

                # # Set database schema if using schema-based multi-tenancy
                # if getattr(settings, 'MULTI_TENANT', False):
                #     connection.set_schema(getattr(school, 'schema_name', 'public'))
                set_current_request(request)
            else:
                # Handle missing school
                set_current_request(request)
                return self._handle_missing_school(request)

        except Exception as e:
            set_current_request(None)
            return self._handle_error(request, e)

        return None

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Process response and clean up context."""
        # Log the request
        self._log_request(request, response)

        # Clean up context
        set_current_school(None)
        set_current_request(None)

        # Reset schema if using schema-based multi-tenancy
        if getattr(settings, 'MULTI_TENANT', False):
            connection.set_schema_to_public()

        return response

    def _resolve_school(self, request: HttpRequest) -> Optional[School]:
        """Resolve school using multiple strategies."""
        # Strategy 1: Subdomain resolution
        host = request.get_host()
        print("\n\nhost", host)

        # Try BASE_DOMAIN approach first
        base_domain = getattr(settings, 'BASE_DOMAIN', None) or getattr(
            settings, 'TENANCY_BASE_DOMAIN', None)
        if base_domain:
            subdomain = TenantResolver.extract_from_base_domain(
                host, base_domain)
        else:
            subdomain = TenantResolver.extract_subdomain_from_host(host)

        if subdomain:
            school = TenantResolver.lookup_school(subdomain)
            if school:
                return school

        # Debug: Print all headers and META data
        print("\n\n===== REQUEST HEADERS =====")
        for header, value in request.META.items():
            if header.startswith('HTTP_') or header.startswith('AUTHORIZATION') or header in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                print(f"{header}: {value}")
        # print("\n\n===== ALL META DATA =====")
        # for key, value in request.META.items():
        #     print(f"{key}: {value}")
        print("\n\n")

        # Strategy 2: HTTP_X_SCHOOL header (for API/testing)
        school_header = request.META.get('HTTP_X_SCHOOL')
        print("\n\n\nschool_header", school_header)
        if school_header:
            school = TenantResolver.lookup_school(school_header)
            if school:
                return school

        # Strategy 3: X-School header (alternative)
        school_header_alt = request.headers.get('X-School')
        if school_header_alt:
            school = TenantResolver.lookup_school(school_header_alt)
            if school:
                return school

        return None

    def _should_skip_processing(self, request: HttpRequest) -> bool:
        """Determine if tenant processing should be skipped."""
        print(request.path, request.get_host())
        # Skip for certain paths that aren't in DO_NOT_SKIP_PATHS
        for path in self.SKIP_PATHS:
            if path in request.path:
                # Check if this path should not be skipped
                if any(skip_path in request.path for skip_path in self.DO_NOT_SKIP_PATHS):
                    return False
                return True

        # Skip for system subdomains
        host = request.get_host()
        subdomain = TenantResolver.extract_subdomain_from_host(host)
        if subdomain in self.SYSTEM_SUBDOMAINS:
            return True

        return False

    def _handle_missing_school(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Handle cases where no school is found."""
        # Allow certain endpoints to work without school context
        global_endpoints = ['/api/health/', '/admin/']
        if any(request.path.startswith(endpoint) for endpoint in global_endpoints):
            return None

        if settings.DEBUG:
            return JsonResponse({
                'error': 'No school found for this request',
                'host': request.get_host(),
                'path': request.path,
                'headers': dict(request.headers)
            }, status=400)
        
        print("School not found in UnifiedTenantMiddleware")

        raise Http404("School not found")

    def _handle_error(self, request: HttpRequest, error: Exception) -> HttpResponse:
        """Handle errors during tenant resolution."""
        user_id = getattr(request.user, 'id', 'anonymous') if hasattr(
            request, 'user') else 'anonymous'

        audit_logger.error(
            f"Error resolving tenant: {str(error)}",
            exc_info=True,
            extra={
                'user_id': str(user_id),
                'path': request.path,
                'method': request.method,
                'host': request.get_host()
            }
        )

        if settings.DEBUG:
            return JsonResponse({
                'error': 'Tenant resolution error',
                'detail': str(error)
            }, status=500)

        raise Http404("Service temporarily unavailable")

    def _log_request(self, request: HttpRequest, response: HttpResponse) -> None:
        """Log request details for audit purposes."""
        if not hasattr(request, '_request_start_time'):
            return

        # Skip logging for static files and health checks
        if any(path in request.path for path in ['/static/', '/media/', '/health/']):
            return

        duration = time.time() - request._request_start_time
        user = getattr(request, 'user', None)
        school = get_current_school()

        # Log the request
        audit_logger.info(
            f"{request.method} {request.path} - {response.status_code} - {duration:.3f}s",
            extra={
                'user_id': str(user.id) if user and hasattr(user, 'id') and user.is_authenticated else 'anonymous',
                'school_id': str(school.id) if school else 'none',
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'response_time': duration,
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )

        request_id = datetime.now()
        if hasattr(request, 'request_id'):
            request_id = request.request_id
        if hasattr(request, 'id'):
            request_id = request.id

        AuditLog.objects.create(
            user=user if user and user.is_authenticated else None,
            school=school,
            action="request",
            model="request",
            object_id=str(request_id),
            changes={},
            content_type_id="1",
            extra={
                'user_id': str(user.id) if user and hasattr(user, 'id') and user.is_authenticated else 'anonymous',
                'school_id': str(school.id) if school else 'none',
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'response_time': duration,
                'ip_address': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            }
        )

        # Log errors and warnings
        if 400 <= response.status_code < 500:
            audit_logger.warning(
                f"Client error {response.status_code} on {request.method} {request.path}",
                extra={
                    'user_id': str(user.id) if user and hasattr(user, 'id') and user.is_authenticated else 'anonymous',
                    'school_id': str(school.id) if school else 'none',
                }
            )
        elif response.status_code >= 500:
            audit_logger.error(
                f"Server error {response.status_code} on {request.method} {request.path}",
                extra={
                    'user_id': str(user.id) if user and hasattr(user, 'id') and user.is_authenticated else 'anonymous',
                    'school_id': str(school.id) if school else 'none',
                }
            )

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


# Keep this for backward compatibility if needed
class RequestThreadLocalMiddleware(MiddlewareMixin):
    """Simple middleware to manage request thread locals. 
        Push/pop the current request to thread‑locals around the view.
    """

    def process_request(self, request: HttpRequest) -> None:
        set_current_request(request)

    # Clear only the request; school can persist for tasks if explicitly set.
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        set_current_request(None)
        return response


class AppendSlashMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Ignore URLs that are explicitly marked with no-slash or already have a slash
        if request.path.endswith('/') or '.' in request.path.split('/')[-1]:
            return None

        # Check if the URL should end with a slash
        if settings.APPEND_SLASH and not request.path.endswith('/'):
            # Build the new URL with a slash appended
            new_url = f"{request.path}/"
            if request.GET:
                new_url += f"?{request.META['QUERY_STRING']}"
            return HttpResponsePermanentRedirect(new_url)

        return None
