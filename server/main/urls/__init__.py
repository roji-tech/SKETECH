# from main.views import *
# from main.views.class_note_views import *

# from .superadmin_url import urlpatterns as superadmins_urlpatterns
# from .student_urls import urlpatterns as students_urlpatterns
# from .admin_url import urlpatterns as admins_urlpatterns
# from .auth_url import urlpatterns as auth_urlpatterns

# from .teachers_url import auth_urlpatterns as teachers_urlpatterns
# from django.urls import path
# from django.views.generic import TemplateView
# from main.views.settings import SettingView

urlpatterns = [
    # path("accounts/login/", TemplateView.as_view(template_name="signin.html"), name='logout'),
    # path("", TemplateView.as_view(template_name="index.html"), name="home"),
    # path('logout/', LogoutRedirectView.as_view(), name='logout_redirect'),
    # path('dashboard/', DashboardRedirectView.as_view(), name='dashboard_redirect'),
    # path("test/", TemplateView.as_view(template_name="test.htm"), name="test"),
]

# urlpatterns += teachers_urlpatterns
# urlpatterns += admins_urlpatterns
# urlpatterns += students_urlpatterns
# urlpatterns += superadmins_urlpatterns
# urlpatterns += auth_urlpatterns


urlpatterns += [
    # path('profile/update/', edit_profile, name='edit_profile'),
    # path('profile/', profile_settings, name='profile'),

    # # GmeetClass URLs
    # path('gmeet-classes/', GmeetClassListView.as_view(), name='gmeetclass-list'),
    # path('gmeet-classes/<int:pk>/',
    #      GmeetClassDetailView.as_view(), name='gmeetclass-detail'),
    # path('gmeet-classes/create/', GmeetClassCreateView.as_view(),
    #      name='gmeetclass-create'),
    # path('gmeet-classes/<int:pk>/update/',
    #      GmeetClassUpdateView.as_view(), name='gmeetclass-update'),
    # path('gmeet-classes/<int:pk>/delete/',
    #      GmeetClassDeleteView.as_view(), name='gmeetclass-delete'),

    # # LessonPlan URLs
    # path('lesson-plans/', LessonPlanListView.as_view(), name='list-lessonplans'),
    # path('lesson-plans/<int:pk>/', LessonPlanDetailView.as_view(),
    #      name='lessonplan-detail'),
    # path('lesson-plans/create/', LessonPlanCreateView.as_view(),
    #      name='lessonplan-create'),
    # path('lesson-plans/<int:pk>/update/',
    #      LessonPlanUpdateView.as_view(), name='lessonplan-update'),
    # path('lesson-plans/<int:pk>/delete/',
    #      LessonPlanDeleteView.as_view(), name='lessonplan-delete'),

    # # ClassNote URLs
    # path('class-notes/', ClassNoteListView.as_view(), name='classnote-list'),
    # path('class-notes/<int:pk>/', ClassNoteDetailView.as_view(),
    #      name='classnote-detail'),
    # path('class-notes/create/', class_note_create,
    #      name='classnote-create'),
    # path('class-notes/<int:pk>/update/',
    #      ClassNoteUpdateView.as_view(), name='classnote-update'),
    # path('class-notes/<int:pk>/delete/',
    #      ClassNoteDeleteView.as_view(), name='classnote-delete'),


    # path('comingsoon/',
    #      TemplateView.as_view(template_name="comingsoon.html"), name='comingsoon'),
]
