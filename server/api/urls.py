from django.urls import path, include

from rest_framework_nested import routers
# from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import token_refresh, token_verify, token_obtain_pair

from api.views import LogoutView
from api.views.auth_views import get_school_info
# from api.views.attendance_views import AttendanceViewSet, OvertimeViewSet, AttendanceReportView
from api import views
from api.views.other_views import DashboardView


router = routers.DefaultRouter()
router.register('schools', views.SchoolViewSet, basename='schools'),
router.register('academic-sessions', views.AcademicSessionViewSet,
                basename='academic_session')
router.register('staff', views.StaffViewSet, basename='staff')
router.register('students', views.StudentViewSet, basename='students')
router.register('classes', views.ClassListViewSet, basename='classes')

# Register attendance routes
# router.register('attendance', AttendanceViewSet, basename='attendance')
# router.register('overtime', OvertimeViewSet, basename='overtime')

# Nested routers for Academic session
academic_sessions_router = routers.NestedSimpleRouter(
    router, 'academic-sessions', lookup='academic_session')
academic_sessions_router.register(
    'terms', views.TermViewSet, basename='academic-session-terms')

# Nested Router for Schools
school_router = routers.NestedSimpleRouter(router, 'schools', lookup='school')
school_router.register('classes', views.ClassListViewSet,
                       basename='school-classes')

# Nested Router for Attendance
# attendance_router = routers.NestedSimpleRouter(router, 'attendance', lookup='attendance')
# attendance_router.register('activities', AttendanceViewSet, basename='attendance-activities')
# attendance_router.register('reports', AttendanceReportView, basename='attendance-reports')

urlpatterns = [
    # Main API routes
    path('', include(router.urls)),
    
    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # Nested routes
    path('', include(academic_sessions_router.urls)),
    path('', include(school_router.urls)),
    # path('', include(attendance_router.urls)),
    
    # School info
    path('school_info/', get_school_info),

    # Authentication
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.jwt")),
    path("auth/logout/", LogoutView.as_view()),
    path("auth/login/", token_obtain_pair, name="token_obtain_pair"),
    path("auth/token/refresh/", token_refresh, name="token_refresh"),
    
    # Attendance Reports
    # path('reports/attendance/', AttendanceReportView.as_view(), name='attendance-reports'),
    
    # Include default auth views for the browsable API
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    # Include the attendance app's URLs
    # path('attendance/', include('attendance.urls')),
]
