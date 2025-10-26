from django.core.management.base import BaseCommand
from sportlibrary.models import Sport
from gearguide.models import Gear
import json
from pathlib import Path

class Command(BaseCommand):
    help = "Sinkronisasi data gear dari JSON ke database berdasarkan mapping sport_id → sport_name"

    def handle(self, *args, **kwargs):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        json_path = base_dir / "database" / "gears.json"

        if not json_path.exists():
            self.stdout.write(self.style.ERROR("❌ File gears.json tidak ditemukan!"))
            return

        # 🧭 Manual mapping sport_id → sport_name
        SPORT_MAP = {
            1: "Bulu Tangkis",
            2: "Yoga",
            3: "Tenis",
            4: "Renang",
            5: "Panahan",
            6: "Lari",
            7: "Basket",
            8: "Futsal",
            9: "Bersepeda",
            10: "Tenis Meja",
            11: "Voli",
            12: "Panjat Tebing",
            13: "Muay Thai",
            14: "Golf",
            15: "Selancar",
            16: "Pencak Silat",
            17: "Baseball",
            18: "Skateboard",
            19: "Calisthenics",
            20: "Wall Climbing Indoor",
        }

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        level_map = {
            'Pemula': 'beginner',
            'Menengah': 'intermediate',
            'Lanjutan': 'advanced',
            # Tambahkan value huruf kecil jika ada data yang tidak konsisten
            'pemula': 'beginner', 
            'menengah': 'intermediate',
            'lanjutan': 'advanced',
        }

        created, skipped = 0, 0
        for gear_data in data:
            try:
                sport_id = gear_data.get("sport_id")
                sport_name = SPORT_MAP.get(sport_id, "Tidak diketahui")

                level_raw = gear_data.get("level", "Pemula") # Ambil "Pemula"
                level_db = level_map.get(level_raw, 'beginner')

                # Cari sport by name (buat kalau udah ada di DB)
                sport_obj = Sport.objects.filter(name__iexact=sport_name).first()
                if not sport_obj:
                    sport_obj, _ = Sport.objects.get_or_create(
                        name=sport_name,
                        defaults={
                            "category": "Umum",
                            "difficulty": "beginner",
                            "description": "Auto-created from gear sync",
                            "level": level_db,
                        }
                    )

                Gear.objects.update_or_create(
                    name=gear_data["name"],
                    defaults={
                        "sport": sport_obj,
                        "function": gear_data.get("function", ""),
                        "description": gear_data.get("description", ""),
                        "level": gear_data.get("level", "Pemula").lower(),
                        "price_range": gear_data.get("price_range", "-"),
                        "recommended_brands": gear_data.get("recommended_brands", []),
                        "materials": gear_data.get("materials", []),
                        "care_tips": gear_data.get("care_tips", ""),
                        "ecommerce_link": gear_data.get("buy_link", ""),
                        "tags": gear_data.get("tags", []),
                        "image": gear_data.get("image", ""),
                        "owner": None,
                    },
                )

                created += 1
                self.stdout.write(self.style.SUCCESS(f"✅ {gear_data['name']} ({sport_name})"))

            except Exception as e:
                skipped += 1
                self.stdout.write(self.style.ERROR(f"⚠️ Gagal import {gear_data.get('name')}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\n🎯 Import selesai! {created} berhasil, {skipped} gagal."))
