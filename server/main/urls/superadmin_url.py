from django.urls import path
from ..views import SuperAdminHome

urlpatterns = [
    path('skesuperadmin/', SuperAdminHome.as_view(), name='superadmin_home'),
]
