from django.urls import path
from . import views

app_name = 'notification'

urlpatterns = [
  path('', views.notification_center, name='notifications')
]