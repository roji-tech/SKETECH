from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_quiz, name='create_quiz'),
    path('<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('result/<int:score>/', views.quiz_result, name='quiz_result'),
    path('<int:quiz_id>/questions/', views.add_question, name='add-question'),
    path('<int:pk>/', views.QuizDetailView.as_view(), name='quiz_detail'),
]
