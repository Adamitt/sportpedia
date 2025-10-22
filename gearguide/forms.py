from django import forms
from .models import Gear

class GearForm(forms.ModelForm):
    class Meta:
        model = Gear
        fields = ['sport', 'name', 'function', 'description', 'price_range', 'level']
