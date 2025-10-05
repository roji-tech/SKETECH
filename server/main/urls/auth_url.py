from django.contrib.auth import views
from django.urls import path
from main.views import login_views, LogoutRedirectView

urlpatterns = [
    path(
        'admin/login/',
        login_views.AdminLoginView.as_view(),
        name='admin-login'
    ),
    path(
        'skesuperadmin/login',
        login_views.SuperAdminLoginView.as_view(),
        name='superadmin-login'
    ),

    path(
        'staff/login/',
        login_views.TeacherLoginView.as_view(),
        name='teacher-login'
    ),
    path(
        'students/login/',
        login_views.StudentLoginView.as_view(),
        name='student-login'
    ),
    #     path('staff/edit-gmeet/', views.staff_edit_gmeet, name='edit_gmeet'),

    #     path('staff/upload-lesson/', views.upload_lesson_plan,
    #          name='upload_lesson_plan'),
    #     path('staff/lessons-lists/', views.lessons_list, name='lessons_lists'),

    # path('staff/add-assessment/', views.continous_assessment_view, name='continous-assessment'),
]

# The views used below are normally mapped in the AdminSite instance.
# This URLs file is used to provide a reliable view deployment for test purposes.
# It is also provided as a convenience to those who want to deploy these URLs
# elsewhere.


urlpatterns += [
    path("logout/", LogoutRedirectView.as_view(), name="logout"),
    path(
        "password_change/", views.PasswordChangeView.as_view(), name="password_change"
    ),
    path(
        "password_change/done/",
        views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path("password_reset/", views.PasswordResetView.as_view(), name="password_reset"),
    path(
        "password_reset/done/",
        views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
