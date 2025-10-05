from django.urls import path

from ..views import StudentsHome
from library.views import *
from main.views.student_views import StudentClassNoteListView, StudentGoogleMeetListView, class_list_view, e_exam


urlpatterns = [
    path('students/', StudentsHome.as_view(), name='students'),


    path('students/view-google-classes/', StudentGoogleMeetListView.as_view(), name='google_meets_classes'),

    path('total-students/', StudentsHome.as_view(), name='total_students'),

    path('student/subjects/combination', StudentsHome.as_view(), name='student_subject_combination'),

    path('students/class-notes/', StudentClassNoteListView.as_view(), name='students_class_notes'),

    path('students/my-class-list/', class_list_view, name='class_list_view'),

    path('students/exam-view/', e_exam, name='exam_login'),
]