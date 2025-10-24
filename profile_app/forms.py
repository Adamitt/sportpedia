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
    foto_profil = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'accept': 'image/*', 'class': 'block w-full text-sm text-gray-500 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 transition duration-150 ease-in-out'}))

    class Meta:
        model = UserProfile
        fields = ['foto_profil', 'olahraga_favorit', 'preferensi']