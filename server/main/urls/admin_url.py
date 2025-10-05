from django.urls import path

from main.views.admin_views import (

    AddSession, ClassCreateView, ClassDeleteView, ClassListView,

    ClassUpdateView, DeleteSession, ListSession,

    StudentCreateView,

    StudentDeleteView, StudentListView, StudentUpdateView, SubjectCreateView,

    SubjectDeleteView, SubjectListView, SubjectUpdateView, StaffCreateView,

    TeacherDeleteView, StaffListView, StaffUpdateView, UpdateSession,

    GmeetListView, session_detail_view, edit_term_view, add_term_view, add_edit_term, create_classes_view
)

from main.views.auth_views import activate_account

from ..views import AdminsHome, RegisterAndRegisterSchool, AdminsHelp

urlpatterns = [
    path('activate/<uidb64>/<token>/', activate_account, name='activate'),

    path('admin/', AdminsHome.as_view(), name='myadmin'),
    path('admin/register/', RegisterAndRegisterSchool.as_view(),
         name='signup'),
    path('admin/help/', AdminsHelp.as_view(), name='admin-help'),


    # ACADEMIC SESSIONS
    path('admin/sessions/', ListSession.as_view(), name='list-sessions'),
    path('admin/sessions/add/', AddSession.as_view(), name='add-session'),
    path('admin/sessions/<int:pk>/update/',
         UpdateSession.as_view(), name='update-session'),
    path('admin/sessions/<int:pk>/delete/',
         DeleteSession.as_view(), name='delete-session'),
    path('admin/sessions/<int:pk>/',
         session_detail_view, name='session_detail'),
    path('admin/term/<int:session_id>/setup/',
         create_classes_view, name='create_classes'),
    path('admin/term/<int:session_id>/', add_term_view, name='add_term'),
    path('admin/term/<int:session_id>/<int:term_id>/',
         edit_term_view, name='edit_term'),
    #     path('admin/term/add/<int:pk>/', add_term_view, name='add_term'),


    # CLASSES
    path('admin/classes/', ClassListView.as_view(), name='list-classes'),
    path('admin/classes/add/', ClassCreateView.as_view(), name='add-class'),
    path('admin/classes/<int:pk>/update/',
         ClassUpdateView.as_view(), name='update-class'),
    path('admin/classes/<int:pk>/delete/',
         ClassDeleteView.as_view(), name='delete-class'),



    # SUBJECTS
    path("admin/subjects/", SubjectListView.as_view(), name="list-subjects"),
    path("admin/subjects/add/", SubjectCreateView.as_view(), name="add-subject"),
    path('admin/subjects/<int:pk>/update/',
         SubjectUpdateView.as_view(), name='update-subject'),
    path('admin/subjects/<int:pk>/delete/',
         SubjectDeleteView.as_view(), name='delete-subject'),



    # STUDENTS

    path("admin/students/", StudentListView.as_view(), name="list-students"),
    path("admin/students/add/", StudentCreateView.as_view(), name="add-student"),
    path('admin/students/<int:pk>/update/',
         StudentUpdateView.as_view(), name='update-student'),
    path('admin/students/<int:pk>/delete/',
         StudentDeleteView.as_view(), name='delete-student'),



    # TEACHERS

    path("admin/staff/",  StaffListView.as_view(), name="list-staff"),
    path("admin/staff/add/",  StaffCreateView.as_view(), name="add-staff"),
    path('admin/staff/<int:pk>/update/',
         StaffUpdateView.as_view(), name='update-staff'),
    path('admin/staff/<int:pk>/delete/',

         TeacherDeleteView.as_view(), name='delete-staff'),


    # OTHERS

    #     path("admin/lesson-plans/", GmeetListView.as_view(), name="list-lesson_plans"),

    #     path("admin/notes/", GmeetListView.as_view(), name="list-notes"),
]
