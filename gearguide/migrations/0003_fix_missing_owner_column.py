from django.db import migrations

def ensure_owner_id_column(apps, schema_editor):
    connection = schema_editor.connection
    cursor = connection.cursor()

    # cek apakah kolom sudah ada
    cursor.execute("PRAGMA table_info(gearguide_gear);")
    cols = [row[1] for row in cursor.fetchall()]
    if 'owner_id' in cols:
        return  # sudah ada, beres

    # Tambah kolom (SQLite)
    cursor.execute("PRAGMA foreign_keys=OFF;")
    cursor.execute("ALTER TABLE gearguide_gear ADD COLUMN owner_id integer NULL;")
    cursor.execute("PRAGMA foreign_keys=ON;")

class Migration(migrations.Migration):

    dependencies = [
        ('gearguide', '0002_initial'),  # ⬅️ sesuaikan jika perlu
    ]

    operations = [
        migrations.RunPython(ensure_owner_id_column, reverse_code=migrations.RunPython.noop),
    ]
