from django.urls import path
from report.views import update_complaint
from . import views

urlpatterns = [
    path('', views.submit_complaint, name='complaints'),
    path('<str:pk>/', views.update_complaint, name='complaints'),
    path('submit/', views.submit_complaint, name='submit_complaint'),
]
