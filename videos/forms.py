from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Video, Sport

class VideoForm(forms.ModelForm):
    """
    Form untuk Video model yang menggunakan URL (bukan upload file).
    """
    
    # Buat field 'tags' menjadi CharField agar mudah diisi di form
    tags_string = forms.CharField(
        label="Tags (pisahkan dengan koma)",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]',
            'placeholder': 'cth: climb, technique, beginner'
        })
    )

    class Meta:
        model = Video
        # Sesuaikan field dengan models.py Anda yang baru
        fields = [
            'title', 
            'description', 
            'sport', 
            'difficulty', 
            'video_url', 
            'thumbnail_url', # <-- Gunakan ini
            'instructor',    # <-- Gunakan ini
            'duration',
            'tags_string',   # <-- Gunakan field CharField kustom
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]',
                'placeholder': 'Judul video (min. 5 karakter)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]',
                'rows': 4,
                'placeholder': 'Deskripsi lengkap video (min. 20 karakter)'
            }),
            'sport': forms.Select(attrs={
                'class': 'w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]'
            }),
            'difficulty': forms.Select(attrs={
                'class': 'w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]'
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]',
                'placeholder': 'https://www.youtube.com/watch?v=...'
            }),
            'thumbnail_url': forms.URLInput(attrs={
                'class': 'w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]',
                'placeholder': 'https://img.youtube.com/vi/... (Otomatis jika YouTube)'
            }),
            'instructor': forms.TextInput(attrs={
                'class': 'w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]',
                'placeholder': 'Nama instruktur'
            }),
            'duration': forms.TextInput(attrs={
                'class': 'w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]',
                'placeholder': 'Format: MM:SS (contoh: 05:30)'
            }),
        }
        
        labels = {
            'title': 'Judul Video',
            'description': 'Deskripsi',
            'sport': 'Kategori Olahraga',
            'difficulty': 'Tingkat Kesulitan',
            'video_url': 'URL Video (YouTube)',
            'thumbnail_url': 'URL Thumbnail (Opsional)',
            'instructor': 'Instruktur',
            'duration': 'Durasi Video'
        }
        
        help_texts = {
            'thumbnail_url': 'Akan diisi otomatis dari URL YouTube jika dibiarkan kosong.',
            'duration': 'Durasi video dalam format MM:SS (contoh: 05:30)',
            'video_url': 'Wajib diisi. Pastikan link YouTube valid.'
        }
    
    def __init__(self, *args, **kwargs):
        """Isi 'tags_string' saat mengedit (load instance)"""
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.tags:
                self.fields['tags_string'].initial = ', '.join(self.instance.tags)

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title or len(title.strip()) < 5:
             raise ValidationError('Judul harus minimal 5 karakter.')
        return title.strip()
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description or len(description.strip()) < 20:
             raise ValidationError('Deskripsi harus minimal 20 karakter.')
        return description.strip()
    
    def clean_duration(self):
        duration = self.cleaned_data.get('duration')
        if not duration: raise ValidationError('Durasi tidak boleh kosong.')
        pattern = r'^\d{1,2}:\d{2}$'
        if not re.match(pattern, duration): raise ValidationError('Format durasi harus MM:SS (contoh: 05:30)')
        return duration
    
    def clean_video_url(self):
        video_url = self.cleaned_data.get('video_url')
        if not video_url:
             raise ValidationError('URL Video tidak boleh kosong.')
        
        # Validasi YouTube (dari form Anda sebelumnya)
        youtube_patterns = [r'youtube\.com/watch\?v=', r'youtu\.be/', r'youtube\.com/embed/']
        is_youtube = any(re.search(pattern, video_url) for pattern in youtube_patterns)
        if not is_youtube:
            raise ValidationError('URL harus dari YouTube (youtube.com atau youtu.be)')
        return video_url
    
    def clean(self):
        """Auto-generate thumbnail"""
        cleaned_data = super().clean()
        video_url = cleaned_data.get('video_url')
        thumbnail_url = cleaned_data.get('thumbnail_url')
        
        if video_url and not thumbnail_url:
            video_id = None
            if 'v=' in video_url: video_id = video_url.split('v=')[-1].split('&')[0]
            elif 'youtu.be/' in video_url: video_id = video_url.split('youtu.be/')[-1].split('?')[0]
            
            if video_id and len(video_id) == 11:
                cleaned_data['thumbnail_url'] = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
        return cleaned_data

    def save(self, commit=True):
        """Simpan tags_string ke field 'tags' (JSONField)"""
        instance = super().save(commit=False)
        tags_str = self.cleaned_data.get('tags_string', '')
        instance.tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        
        if commit:
            instance.save()
        return instance