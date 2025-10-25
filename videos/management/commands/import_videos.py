import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from videos.models import Video
from sportlibrary.models import Sport

class Command(BaseCommand):
    help = 'Import videos dari videos.json ke database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='videos/data/videos.json',
            help='Path ke file videos.json'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Hapus semua video yang ada sebelum import'
        )

    def handle(self, *args, **options):
        json_file = options['file']
        clear_existing = options['clear']
        
        self.stdout.write(self.style.WARNING(f'📥 Mengimport videos dari {json_file}...'))
        
        # Hapus video yang sudah ada jika diminta
        if clear_existing:
            count = Video.objects.count()
            Video.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'🗑️  Menghapus {count} video yang ada'))
        
        # Load data dari JSON
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                videos_data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'❌ File tidak ditemukan: {json_file}'))
            return
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'❌ JSON tidak valid: {e}'))
            return
        
        # Ambil atau buat user admin default sebagai uploader
        uploader, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'is_staff': True,
                'is_superuser': True,
                'email': 'admin@sportpedia.com'
            }
        )
        
        if created:
            uploader.set_password('admin123')  # Set password default
            uploader.save()
            self.stdout.write(self.style.SUCCESS('✅ User admin default berhasil dibuat'))
        
        # Mapping difficulty dari Bahasa Indonesia ke English
        difficulty_map = {
            'Pemula': 'beginner',
            'Menengah': 'intermediate',
            'Lanjutan': 'advanced',
            'Profesional': 'advanced',
        }
        
        # Counter untuk tracking
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        # Loop setiap video dari JSON
        for video_data in videos_data:
            try:
                # Ambil sport berdasarkan sport_id
                sport_id = video_data.get('sport_id')
                try:
                    sport = Sport.objects.get(id=sport_id)
                except Sport.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Sport ID {sport_id} tidak ditemukan, skip video: {video_data.get("title")}')
                    )
                    skipped_count += 1
                    continue
                
                # Convert difficulty dari Indonesia ke English
                difficulty_raw = video_data.get('difficulty', 'Pemula')
                difficulty = difficulty_map.get(difficulty_raw, 'beginner')
                
                # Ambil URL dan thumbnail
                video_url = video_data.get('url', '')
                thumbnail_url = video_data.get('thumbnail', '')
                
                # Generate thumbnail YouTube otomatis jika belum ada
                if not thumbnail_url and 'youtube.com' in video_url:
                    video_id = video_url.split('v=')[-1].split('&')[0]
                    thumbnail_url = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
                
                # Cek apakah video sudah ada (berdasarkan judul dan sport)
                existing = Video.objects.filter(
                    title=video_data.get('title'),
                    sport=sport
                ).first()
                
                if existing:
                    self.stdout.write(
                        self.style.WARNING(f'⏭️  Video sudah ada: {video_data.get("title")}')
                    )
                    skipped_count += 1
                    continue
                
                # Buat video baru
                video = Video.objects.create(
                    title=video_data.get('title', 'Untitled'),
                    description=video_data.get('description', ''),
                    sport=sport,
                    difficulty=difficulty,
                    video_url=video_url,
                    duration=video_data.get('duration', '00:00'),
                    uploader=uploader,
                    views_count=video_data.get('views', 0)
                )
                
                imported_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Berhasil import: {video.title} ({sport.name})')
                )
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Error saat import {video_data.get("title", "Unknown")}: {str(e)}')
                )
        
        # Tampilkan summary hasil import
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✅ Berhasil diimport: {imported_count} videos'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'⏭️  Diskip: {skipped_count} videos'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ Error: {error_count} videos'))
        self.stdout.write('='*60)
        
        if imported_count > 0:
            self.stdout.write('\n' + self.style.SUCCESS('🎉 Import selesai!'))
            self.stdout.write(self.style.WARNING('💡 Jalankan migrations jika diperlukan: python manage.py migrate'))