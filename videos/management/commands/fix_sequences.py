from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Memperbaiki ID sequence (penghitung) di PostgreSQL setelah impor data manual.'

    def handle(self, *args, **options):
        # Daftarkan semua tabel yang ID-nya diimpor manual dari JSON
        tables_to_fix = [
            'videos_video',
            'sportlibrary_sport',
            'gearguide_gear',
            # Tambahkan model lain jika perlu
        ]

        self.stdout.write(self.style.WARNING('Memulai perbaikan ID sequences...'))

        with connection.cursor() as cursor:
            for table_name in tables_to_fix:
                self.stdout.write(f'Memperbaiki {table_name}...')
                try:
                    # Dapatkan nama sequence (penghitung)
                    cursor.execute(f"SELECT pg_get_serial_sequence('\"{table_name}\"', 'id')")
                    sequence_name_result = cursor.fetchone()

                    if not sequence_name_result or not sequence_name_result[0]:
                        self.stdout.write(self.style.WARNING(f'  -> Melewatkan {table_name} (ID mungkin bukan AutoField/Serial).'))
                        continue

                    sequence_name = sequence_name_result[0]

                    # Atur sequence ke nilai max(id) + 1
                    sql_reset = f"""
                    SELECT setval(
                        '{sequence_name}', 
                        (SELECT COALESCE(MAX(id), 1) FROM "{table_name}"), 
                        (SELECT MAX(id) IS NOT NULL FROM "{table_name}")
                    );
                    """
                    cursor.execute(sql_reset)
                    self.stdout.write(self.style.SUCCESS(f'  -> Sequence {table_name} berhasil direset.'))

                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'  -> GAGAL mereset {table_name}: {e}'))

        self.stdout.write(self.style.SUCCESS('\nSelesai. Penghitung ID sudah diperbarui.'))