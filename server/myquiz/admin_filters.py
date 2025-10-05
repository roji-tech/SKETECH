from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Quiz, AcademicSession  # Adjust to your models


class AcademicSessionFilter(admin.SimpleListFilter):
    title = _('Academic Session')  # Title for the filter
    parameter_name = 'academic_session'  # Query param name in the URL

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. Each tuple contains the value 
        as passed to the queryset, and the display name.
        """
        sessions = AcademicSession.get_school_sessions(request)
        return [(session.id, session.name) for session in sessions]

    def queryset(self, request, queryset):
        # sessions = queryset.get_school_sessions(request)
        """
        Filters the queryset based on the selected value.
        """
        if self.value():
            return queryset.filter(academic_session__id=self.value())
        return queryset


class ActiveQuizFilter(admin.SimpleListFilter):
    title = 'active quizzes'
    parameter_name = 'is_active'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(is_active=True)
        if self.value() == 'inactive':
            return queryset.filter(is_active=False)
