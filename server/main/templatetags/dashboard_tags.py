from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def get_dashboard_url(user):
    if user.is_superuser:
        return reverse('myadmin')
    elif user.groups.filter(name='Teacher').exists():
        return reverse('staff')
    elif user.groups.filter(name='Student').exists():
        return reverse('students')
    return reverse('home')