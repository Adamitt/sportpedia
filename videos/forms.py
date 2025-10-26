from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Video

class VideoForm(forms.ModelForm):
    """
    Enhanced VideoForm dengan validation dan helper text
    """
    
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
                'placeholder': 'https://www.youtube.com/watch?v=... (opsional jika upload file)'
            }),
            'video_file': forms.ClearableFileInput(attrs={
                'class': 'w-full p-3 border rounded-xl text-gray-700 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]',
                'accept': 'video/*'
            }),
            'thumbnail': forms.ClearableFileInput(attrs={
                'class': 'w-full p-3 border rounded-xl text-gray-700 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#1E3A5F]',
                'accept': 'image/*'
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
            'video_file': 'Upload Video File',
            'thumbnail': 'Thumbnail (Opsional)',
            'duration': 'Durasi Video'
        }
        
        help_texts = {
            'video_url': 'Paste link YouTube atau upload file video di bawah',
            'video_file': 'Upload video file (max 100MB) jika tidak menggunakan YouTube',
            'thumbnail': 'Upload gambar untuk thumbnail (opsional, akan auto-generate dari YouTube)',
            'duration': 'Durasi video dalam format MM:SS (contoh: 05:30 untuk 5 menit 30 detik)'
        }
    
    def clean_title(self):
        """Validate title"""
        title = self.cleaned_data.get('title')
        
        if not title or len(title.strip()) < 5:
            raise ValidationError('Judul harus minimal 5 karakter.')
        
        # Check duplicate title for same sport
        sport = self.cleaned_data.get('sport')
        if sport:
            existing = Video.objects.filter(title__iexact=title, sport=sport)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError(f'Video dengan judul "{title}" sudah ada untuk olahraga {sport.name}.')
        
        return title.strip()
    
    def clean_description(self):
        """Validate description"""
        description = self.cleaned_data.get('description')
        
        if not description or len(description.strip()) < 20:
            raise ValidationError('Deskripsi harus minimal 20 karakter.')
        
        return description.strip()
    
    def clean_duration(self):
        """Validate duration format (MM:SS)"""
        duration = self.cleaned_data.get('duration')
        
        if not duration:
            raise ValidationError('Durasi tidak boleh kosong.')
        
        # Check format MM:SS
        pattern = r'^\d{1,2}:\d{2}$'
        if not re.match(pattern, duration):
            raise ValidationError('Format durasi harus MM:SS (contoh: 05:30)')
        
        # Validate minutes and seconds
        try:
            minutes, seconds = duration.split(':')
            minutes = int(minutes)
            seconds = int(seconds)
            
            if seconds >= 60:
                raise ValidationError('Detik harus kurang dari 60.')
            
            if minutes == 0 and seconds == 0:
                raise ValidationError('Durasi tidak boleh 00:00.')
            
        except ValueError:
            raise ValidationError('Format durasi tidak valid.')
        
        return duration
    
    def clean_video_url(self):
        """Validate YouTube URL"""
        video_url = self.cleaned_data.get('video_url')
        
        if video_url:
            # Check if it's a valid YouTube URL
            youtube_patterns = [
                r'youtube\.com/watch\?v=',
                r'youtu\.be/',
                r'youtube\.com/embed/'
            ]
            
            is_youtube = any(re.search(pattern, video_url) for pattern in youtube_patterns)
            
            if not is_youtube:
                raise ValidationError('URL harus dari YouTube (youtube.com atau youtu.be)')
            
            # Extract video ID
            try:
                if 'v=' in video_url:
                    video_id = video_url.split('v=')[-1].split('&')[0]
                elif 'youtu.be/' in video_url:
                    video_id = video_url.split('youtu.be/')[-1].split('?')[0]
                else:
                    raise ValidationError('Tidak bisa mengekstrak video ID dari URL')
                
                # Validate video ID length (YouTube IDs are 11 characters)
                if len(video_id) != 11:
                    raise ValidationError('Video ID YouTube tidak valid')
                    
            except Exception:
                raise ValidationError('Format URL YouTube tidak valid')
        
        return video_url
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        video_url = cleaned_data.get('video_url')
        video_file = cleaned_data.get('video_file')
        
        # At least one of video_url or video_file must be provided
        if not video_url and not video_file:
            raise ValidationError('Harus mengisi URL YouTube atau upload video file.')
        
        # If both provided, prefer video_url
        if video_url and video_file:
            self.add_error('video_file', 'Tidak perlu upload file jika sudah ada URL YouTube.')
        
        return cleaned_data


class VideoFilterForm(forms.Form):
    """
    Form untuk filter video di gallery
    """
    from sportlibrary.models import Sport
    
    sport = forms.ModelChoiceField(
        queryset=Sport.objects.all(),
        required=False,
        empty_label='Semua Olahraga',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    difficulty = forms.ChoiceField(
        choices=[('', 'Semua Level')] + Video.DIFFICULTY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sort = forms.ChoiceField(
        choices=[
            ('popular', 'Paling Populer'),
            ('rating', 'Rating Tertinggi'),
            ('newest', 'Terbaru'),
            ('shortest', 'Terpendek'),
        ],
        required=False,
        initial='popular',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cari video...'
        })
    )