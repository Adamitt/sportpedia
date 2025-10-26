from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class UserUpdateForm(forms.ModelForm):
    # Make email required (it's required by default on User model)
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 ease-in-out sm:text-sm'}))
    # Optional password field
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Biarkan kosong jika tidak berubah', 'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 ease-in-out sm:text-sm'}), required=False)

    class Meta:
        model = User
        fields = ['email', 'password'] # Add 'first_name', 'last_name' if you want to edit them too

class UserProfileForm(forms.ModelForm):
    olahraga_favorit = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'cth: Badminton, Lari', 'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 ease-in-out sm:text-sm'}))
    preferensi = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'cth: Suka olahraga outdoor...', 'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 ease-in-out sm:text-sm resize-none'}))
    foto_profil = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'placeholder': 'https://... (paste link gambar di sini)',
        'class': 'block w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 ease-in-out sm:text-sm'
    }))
    class Meta:
        model = UserProfile
        fields = ['foto_profil', 'olahraga_favorit', 'preferensi']