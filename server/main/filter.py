# filters.py
import django_filters
from .models import Staff


class TeacherFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='filter_by_all', label='Search')

    class Meta:
        model = Staff
        fields = ['q', 'subjects__school_class__name']

    def filter_by_all(self, queryset, name, value):
        return queryset.filter(
            Q(user__first_name__icontains=value) |
            Q(user__last_name__icontains=value) |
            Q(user__email__icontains=value) |
            Q(department__icontains=value)
        )
