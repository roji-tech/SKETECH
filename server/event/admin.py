from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Event


class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'school', 'start_date', 'end_date', 'location')
    list_filter = ('school', 'start_date', 'end_date')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)

    fieldsets = (
        (None, {
            'fields': ('school', 'title', 'description', 'location')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
    )

    # Optional: Inlines for related models (if any)


# Register the models with admin site
admin.site.register(Event, EventAdmin)
