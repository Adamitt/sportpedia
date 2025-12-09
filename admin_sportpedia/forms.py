# admin_sportpedia/forms.py
from django import forms
from django.contrib.auth.models import User

# Base Tailwind classes for inputs
input_classes = 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
checkbox_classes = 'h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500'

class AdminUserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': input_classes}))
    is_staff = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': checkbox_classes}), help_text='Designates whether the user can log into this admin site.')
    is_superuser = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': checkbox_classes}), help_text='Designates that this user has all permissions without explicitly assigning them.')

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'is_staff', 'is_superuser')
        widgets = {
            'username': forms.TextInput(attrs={'class': input_classes}),
            'email': forms.EmailInput(attrs={'class': input_classes}),
        }

    def save(self, commit=True):
        # ... (save logic remains the same) ...
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class AdminUserChangeForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': input_classes}), required=False, help_text="Leave blank to keep the current password.")
    is_staff = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': checkbox_classes}), help_text='Designates whether the user can log into this admin site.')
    is_superuser = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': checkbox_classes}), help_text='Designates that this user has all permissions without explicitly assigning them.')

    class Meta:
        model = User
        fields = ('username', 'email', 'is_staff', 'is_superuser', 'password')
        widgets = {
            'username': forms.TextInput(attrs={'class': input_classes}),
            'email': forms.EmailInput(attrs={'class': input_classes}),
        }

    def save(self, commit=True):
        # ... (save logic remains the same) ...
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user