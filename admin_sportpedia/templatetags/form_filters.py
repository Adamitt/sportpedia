from django import template
from django.forms import CheckboxInput

register = template.Library()

@register.filter(name='is_checkbox')
def is_checkbox(field):
    """
    Mengembalikan True jika widget field adalah CheckboxInput.
    """
    return isinstance(field.widget, CheckboxInput)