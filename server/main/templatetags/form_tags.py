from django.utils.safestring import mark_safe
from django import template
from django.forms.boundfield import BoundField

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Adds a CSS class to a form field's widget.
    """
    # print(dir(field))
    print(field, css_class)
    # Ensure we're dealing with a form field (BoundField)
    if isinstance(field, BoundField):
        existing_classes = field.field.widget.attrs.get('class', '')
        updated_classes = f"{existing_classes} {css_class}".strip()
        return field.as_widget(attrs={"class": updated_classes})
    return field  # Return the field unchanged if it's not a form field
