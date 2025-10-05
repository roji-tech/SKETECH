from .views import SchoolEventListView, EventUpdateView, EventDeleteView, EventDetailView
from django.urls import path
from .views import EventCreateView

urlpatterns = [
    path('events/create/', EventCreateView.as_view(), name='event-create'),

    path('school/<int:school_id>/events/',
         SchoolEventListView.as_view(), name='event-list'),
    path('event/<int:pk>/update/', EventUpdateView.as_view(), name='event-update'),
    path('event/<int:pk>/delete/', EventDeleteView.as_view(), name='event-delete'),
    path('event/<int:pk>/', EventDetailView.as_view(), name='event-detail'),
]
