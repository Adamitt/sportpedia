# sportlibrary/management/commands/sync_sports.py
from django.core.management.base import BaseCommand
from sportlibrary.models import Sport
import json
from pathlib import Path

class Command(BaseCommand):
    help = 'Sync sports from JSON to database'

    def handle(self, *args, **kwargs):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        data_path = base_dir / 'database' / 'sports.json'
        
        with open(data_path, 'r', encoding='utf-8') as file:
            sports_data = json.load(file)
        
        for sport_data in sports_data:
            sport, created = Sport.objects.update_or_create(
                id=sport_data['id'],
                defaults={
                    'name': sport_data['name'],
                    'category': sport_data['category'],
                    'difficulty': sport_data['difficulty'],
                    'description': sport_data['description'],
                    'history': sport_data['history'],
                    'rules': sport_data['rules'],
                    'techniques': sport_data['techniques'],
                    'benefits': sport_data['benefits'],
                    'popular_countries': sport_data['popular_countries'],
                    'tags': sport_data['tags']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {sport.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Updated: {sport.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully synced {len(sports_data)} sports!'))