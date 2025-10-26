from django.core.management.base import BaseCommand
from gearguide.models import Gear
import json
from pathlib import Path

class Command(BaseCommand):
    help = 'Update image field in Gear model from gears.json'

    def handle(self, *args, **kwargs):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        data_path = base_dir / 'database' / 'gears.json'

        if not data_path.exists():
            self.stdout.write(self.style.ERROR(f'File not found: {data_path}'))
            return

        with open(data_path, 'r', encoding='utf-8') as file:
            gears_data = json.load(file)

        updated = 0
        skipped = 0

        for g in gears_data:
            gear_name = g.get("name")
            image_path = g.get("image")
            if not image_path:
                skipped += 1
                continue

            try:
                gear = Gear.objects.filter(name__iexact=gear_name).first()
                if not gear:
                    skipped += 1
                    continue

                # kalau field image di model lo adalah ImageField
                # pastikan pathnya sesuai relatif ke MEDIA_ROOT
                gear.image = image_path
                gear.save()
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"Updated image for {gear.name}: {image_path}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error for {gear_name}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"✅ Done! Updated: {updated}, Skipped: {skipped}"))
