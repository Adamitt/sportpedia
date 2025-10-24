from django import forms
from .models import Video

class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = [
            'title', 
            'description', 
            'sport', 
            'difficulty', 
            'video_url', 
            'video_file', 
            'thumbnail', 
            'duration'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]',
                'placeholder': 'Enter video title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]',
                'rows': 4,
                'placeholder': 'Describe this video...'
            }),
            'sport': forms.Select(attrs={
                'class': 'w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]'
            }),
            'difficulty': forms.Select(attrs={
                'class': 'w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]'
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]',
                'placeholder': 'Paste YouTube URL (optional)'
            }),
            'video_file': forms.ClearableFileInput(attrs={
                'class': 'w-full p-3 border rounded-xl text-gray-700 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]'
            }),
            'thumbnail': forms.ClearableFileInput(attrs={
                'class': 'w-full p-3 border rounded-xl text-gray-700 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]'
            }),
            'duration': forms.TextInput(attrs={
                'class': 'w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]',
                'placeholder': 'e.g. 10:30'
            }),
        }
