from .base import *
from .installed_apps import *
from .middlewares import *
from .cors import *
from .db import *
from .static import *
from .graphiz import *
from .email import *
from .rest_framework import *
from .djoser import *

AUTHENTICATION_BACKENDS = [
    # Replace with the actual path to your backend
    'CONFIG.auth_backend.SchoolEmailBackend',
    # 'CONFIG.auth_backend.SchoolUsernameBackend',
    # 'django.contrib.auth.backends.ModelBackend',  # Default backend
]
