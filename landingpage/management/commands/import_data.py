# landingpage/management/commands/import_data.py

import json
from django.core.management.base import BaseCommand
from django.conf import settings
from sportlibrary.models import Sport
from gearguide.models import Gear

class Command(BaseCommand):
    help = 'Imports data from sports.json and gears.json into the database'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting data import...'))

        # Tentukan path ke file JSON Anda
        sports_json_path = settings.BASE_DIR / "database" / "sports.json"
        gears_json_path = settings.BASE_DIR / "database" / "gears.json"

        # 1. Impor data sports.json
        try:
            with open(sports_json_path, 'r', encoding='utf-8') as f:
                sports_data = json.load(f)
                count = 0
                for item in sports_data:
                    # 'update_or_create' mencegah duplikasi data
                    sport, created = Sport.objects.update_or_create(
                        id=item['id'],
                        defaults={
                            'name': item.get('name', 'No Name'),
                            'description': item.get('description', 'No Description'),
                            'image': item.get('image', ''),
                        }
                    )
                    if created:
                        count += 1
                self.stdout.write(self.style.SUCCESS(f'Successfully imported/updated {len(sports_data)} sports. ({count} new created)'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {sports_json_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred during sport import: {e}'))

        # 2. Impor data gears.json
        try:
            with open(gears_json_path, 'r', encoding='utf-8') as f:
                gears_data = json.load(f)
                count = 0
                for item in gears_data:
                    sport_id = item.get('sport_id')
                    sport_instance = None
                    if sport_id:
                        try:
                            sport_instance = Sport.objects.get(id=sport_id)
                        except Sport.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f"Sport with id={sport_id} not found for gear '{item.get('name')}'. Skipping."))
                            continue

                    gear, created = Gear.objects.update_or_create(
                        id=item['id'],
                        defaults={
                            'name': item.get('name', 'No Name'),
                            'description': item.get('description', 'No Description'),
                            'sport': sport_instance,
                            'image': item.get('image', ''),
                            'price_range': item.get('price_range', ''),
                            'recommended_brands': item.get('recommended_brands', []),
                        }
                    )
                    if created:
                        count += 1
                self.stdout.write(self.style.SUCCESS(f'Successfully imported/updated {len(gears_data)} gears. ({count} new created)'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {gears_json_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred during gear import: {e}'))

        self.stdout.write(self.style.SUCCESS('Data import process finished.'))