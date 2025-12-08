import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings

# --- PENTING: Sesuaikan impor ini ---
# Ganti 'sports' dengan nama aplikasi tempat model 'Sport' Anda berada.
from sportlibrary.models import Sport 
# Ganti 'gearguide' dengan nama aplikasi tempat model 'Gear' Anda berada.
from gearguide.models import Gear 

class Command(BaseCommand):
    help = 'Memuat data olahraga dari file JSON ke database'

    def handle(self, *args, **kwargs):
        # 1. Tentukan path ke file JSON Anda
        # Kita asumsikan file 'database/sports.json' ada di direktori root proyek Anda (BASE_DIR)
        file_path = os.path.join(settings.BASE_DIR, 'database', 'sports.json')
        
        # Ganti path ini jika lokasi file Anda berbeda, misalnya:
        # file_path = os.path.join(settings.BASE_DIR, 'sportpedia', 'database', 'sports.json')

        self.stdout.write(self.style.SUCCESS(f'Mencari file di: {file_path}'))

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('File sports.json tidak ditemukan. Periksa path Anda.'))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('File JSON tidak valid. Periksa formatnya.'))
            return

        # Siapkan counter
        created_count = 0
        updated_count = 0
        gear_link_count = 0

        # 2. Loop setiap item di JSON
        for item in data:
            # Gunakan update_or_create untuk menghindari duplikasi berdasarkan 'name'
            sport_obj, created = Sport.objects.update_or_create(
                name=item['name'],
                defaults={
                    'category': item['category'],
                    'difficulty': item['difficulty'],
                    'description': item['description'],
                    'history': item['history'],
                    'rules': item['rules'],
                    'techniques': item['techniques'],
                    'benefits': item['benefits'],
                    'popular_countries': item['popular_countries'],
                    'tags': item['tags'],
                    # 'image' diabaikan karena tidak ada di JSON dan nullable
                }
            )

            if created:
                created_count += 1
                self.stdout.write(f'Membuat: {sport_obj.name}')
            else:
                updated_count += 1
                self.stdout.write(f'Memperbarui: {sport_obj.name}')

            # 3. Tangani relasi ManyToMany (Gears)
            # Ini harus dilakukan setelah objek dibuat/diperbarui
            if 'gear_ids' in item:
                # Hapus relasi lama (jika ada) untuk memastikan data bersih
                sport_obj.gears.clear() 
                
                for gear_id in item['gear_ids']:
                    try:
                        # Cari Gear berdasarkan ID
                        gear = Gear.objects.get(id=gear_id)
                        # Tambahkan relasi
                        sport_obj.gears.add(gear)
                        gear_link_count += 1
                    except Gear.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f'PERINGATAN: Gear dengan ID {gear_id} tidak ditemukan untuk {sport_obj.name}.'
                        ))

        # 4. Berikan laporan akhir
        self.stdout.write(self.style.SUCCESS(
            f'\n--- SELESAI --- \n'
            f'Total Dibuat: {created_count} \n'
            f'Total Diperbarui: {updated_count} \n'
            f'Total Link Gear Dibuat: {gear_link_count}'
        ))