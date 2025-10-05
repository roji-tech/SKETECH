from .models import Event, School
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, DeleteView, DetailView, CreateView
from django.shortcuts import render, redirect
from .forms import EventForm


class EventCreateView(CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_create.html'
    # Redirect to a list of events or another page after successful creation
    success_url = '/events/'


class SchoolEventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'

    def get_queryset(self):
        # Get events for the current school
        school = School.objects.get(pk=self.kwargs['school_id'])
        return Event.get_school_events(school)


class EventUpdateView(UpdateView):  # Update View
    model = Event
    template_name = 'events/event_form.html'
    fields = ['title', 'description', 'start_date',
              'end_date', 'location', 'school']
    success_url = reverse_lazy('event-list')


class EventDeleteView(DeleteView):  # Delete View
    model = Event
    template_name = 'events/event_confirm_delete.html'
    success_url = reverse_lazy('event-list')


class EventDetailView(DetailView):  # Detail View
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'
