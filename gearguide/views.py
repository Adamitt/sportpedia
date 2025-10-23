from django.urls import reverse #
from metrics.utils import bump_view #
from django.conf import settings #
import json
from pathlib import Path
from uuid import UUID
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Gear
from .forms import GearForm
from sportlibrary.models import Sport
from django.contrib.auth.decorators import login_required


# ======================= DETAIL VIEW =======================
def show_gear_detail(request, gear_id):
    gear = get_object_or_404(Gear, id=gear_id)
    
    # ✅ catat view (gear dari DB)
    key = f"gear:{gear.id}"
    url = reverse("gearguide:card_details", kwargs={"gear_id": str(gear.id)})
    bump_view(
        key,
        title=gear.name,
        url=url,
        category="Gear Guide",
        image=(gear.image or ""),
        request=request,
    )

    context = {
        "title": gear.name,
        "gear": gear,
    }
    return render(request, "gearguide/gear_detail.html", context)


# ======================= SHOW ALL GEARS =======================
def show_all_gears(request):
    from pathlib import Path
    import json

    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    gears_path = BASE_DIR / 'database' / 'gears.json'
    sports_path = BASE_DIR / 'database' / 'sports.json'

    # === Load JSONs ===
    json_gears, json_sports = [], []
    if gears_path.exists():
        with open(gears_path, 'r', encoding='utf-8') as f:
            json_gears = json.load(f)
    if sports_path.exists():
        with open(sports_path, 'r', encoding='utf-8') as f:
            json_sports = json.load(f)

    # === Map sport_id ke nama sport ===
    sport_map = {str(s['id']): s['name'] for s in json_sports}

    # === Load Gear dari DB ===
    db_gears = list(Gear.objects.select_related('sport').all())
    combined_gears = []

    # === JSON ITEMS ===
    for g in json_gears:
        sport_id = str(g.get("sport_id"))
        sport_name = sport_map.get(sport_id, g.get("sport", "Unknown"))

        combined_gears.append({
            "id": g.get("id"),  # Tetap integer untuk JSON
            "sport": sport_name,
            "name": g.get("name"),
            "function": g.get("function"),
            "description": g.get("description"),
            "level": g.get("level"),
            "price_range": g.get("price_range"),
            "recommended_brands": g.get("recommended_brands", []),
            "materials": g.get("materials", []),
            "care_tips": g.get("care_tips", ""),
            "buy_link": g.get("buy_link", ""),
            "tags": g.get("tags", []),
            "image": g.get("image", ""),
            "is_from_db": False,
            "owner": None,
        })

    # === DB ITEMS ===
    for g in db_gears:
        combined_gears.append({
            "id": g.id,  # ✅ UUID object langsung, bukan string!
            "sport": g.sport.name if g.sport else "Unknown",
            "name": g.name,
            "function": g.function,
            "description": g.description,
            "level": g.get_level_display(),
            "price_range": g.price_range,
            "recommended_brands": g.recommended_brands or [],
            "materials": g.materials or [],
            "care_tips": g.care_tips,
            "buy_link": g.ecommerce_link,
            "tags": g.tags or [],
            "image": g.image or "",
            "is_from_db": True,
            "owner": (
                g.owner.username if hasattr(g, "owner") and g.owner
                else "Anonymous"
            ),
        })

    # === FILTERS ===
    sport_filter = request.GET.get('sport')
    level_filter = request.GET.get('level')
    view_filter = request.GET.get('view', 'all')

    if sport_filter:
        combined_gears = [
            g for g in combined_gears
            if sport_filter.lower() == str(g.get("sport", "")).lower()
        ]

    if level_filter:
        combined_gears = [
            g for g in combined_gears
            if g.get("level", "").lower() == level_filter.lower()
        ]

    if view_filter == "your":
        if request.user.is_authenticated:
            combined_gears = [
                g for g in combined_gears
                if g["is_from_db"] and g.get("owner") == request.user.username
            ]
        else:
            combined_gears = []

    # === Dropdown dari sports.json ===
    sports = sorted(set(s['name'] for s in json_sports if s.get('name')))
    
    # ✅ all_sports untuk modal edit
    all_sports_list = []
    
    # Dari DB
    for sport in Sport.objects.all():
        all_sports_list.append({
            'id': str(sport.id),
            'name': sport.name
        })
    
    # Dari JSON (yang belum ada di DB)
    db_sport_ids = [str(s.id) for s in Sport.objects.all()]
    for s in json_sports:
        if str(s['id']) not in db_sport_ids:
            all_sports_list.append({
                'id': str(s['id']),
                'name': s['name']
            })

    return render(request, "gearguide/gearguide.html", {
        "title": "Gear Guide",
        "gears": combined_gears,
        "sports": sports,
        "all_sports": all_sports_list,
        "view_filter": view_filter,
    })


# ======================= CARD DETAILS =======================
# ======================= CARD DETAILS =======================
def card_details(request, gear_id):
    # 🧠 Coba ambil dari DB dulu
    try:
        # kalau ID kamu UUID:
        try:
            gear = get_object_or_404(Gear, id=UUID(gear_id))
        except ValueError:
            gear = get_object_or_404(Gear, id=gear_id)
        
        return render(request, "gearguide/card_details.html", {
            "gear": gear,
            "source": "database"
        })

    except Exception:
        # fallback: cari dari JSON kalau memang nggak ketemu di DB
        base_dir = Path(__file__).resolve().parent.parent.parent
        data_path = base_dir / 'database' / 'gears.json'
        if data_path.exists():
            with open(data_path, 'r', encoding='utf-8') as f:
                gears = json.load(f)
                gear = next((g for g in gears if str(g["id"]) == str(gear_id)), None)
                if gear:
                    return render(request, "gearguide/card_details.html", {
                        "gear": gear,
                        "source": "json"
                    })
        return render(request, "404.html", status=404)




# ======================= ADD GEAR =======================
@login_required(login_url='login')
def add_gear(request):
    if request.method == "POST":
        form = GearForm(request.POST)
        if form.is_valid():
            gear = form.save(commit=False)  # ✅ Belum save ke DB
            
            # ✅ Ambil sport dari form (string ID)
            sport_value = form.cleaned_data.get("sport")

            # 🧩 Konversi string ID ke Sport instance
            if isinstance(sport_value, str):
                from uuid import UUID
                sport_obj = None

                # 1️⃣ Coba parse sebagai UUID (dari DB)
                try:
                    sport_uuid = UUID(sport_value)
                    sport_obj = Sport.objects.filter(id=sport_uuid).first()
                except ValueError:
                    pass  # Bukan UUID, mungkin ID dari JSON

                # 2️⃣ Kalau belum ketemu, cari di JSON berdasarkan ID
                if not sport_obj:
                    base_dir = Path(__file__).resolve().parent.parent.parent
                    sports_path = base_dir / "database" / "sports.json"
                    try:
                        with open(sports_path, "r", encoding="utf-8") as f:
                            sports_json = json.load(f)
                            sport_name = None
                            for s in sports_json:
                                if str(s["id"]) == str(sport_value):
                                    sport_name = s["name"]
                                    break
                            if sport_name:
                                # Cari di DB berdasarkan nama
                                sport_obj = Sport.objects.filter(name__iexact=sport_name).first()
                                if not sport_obj:
                                    # Buat baru otomatis
                                    sport_obj = Sport.objects.create(
                                        name=sport_name,
                                        category=s.get("category", "Umum"),
                                        difficulty=s.get("difficulty", "Menengah"),
                                        description=s.get("description", "Generated otomatis dari JSON."),
                                        history=s.get("history", "Tidak tersedia."),
                                    )
                    except Exception as e:
                        print(f"⚠️ Gagal membaca sports.json: {e}")

                gear.sport = sport_obj
            else:
                gear.sport = sport_value

            # Simpan owner dan gear
            gear.owner = request.user
            gear.save()

            messages.success(request, f"✅ Gear '{gear.name}' berhasil ditambahkan di kategori {gear.sport.name}!")
            return redirect("gearguide:show_all_gears")
        else:
            messages.error(request, "⚠️ Gagal menambahkan gear. Periksa kembali input kamu.")
    else:
        form = GearForm()

    return render(request, "gearguide/add_gear.html", {"form": form})



# ======================= DELETE GEAR =======================
@login_required(login_url='login')
@require_http_methods(["POST"])
def delete_gear(request, gear_id):
    gear = get_object_or_404(Gear, id=gear_id)
    if hasattr(gear, "owner") and gear.owner != request.user:
        messages.error(request, "🚫 Kamu tidak punya izin untuk menghapus gear ini.")
        return redirect("gearguide:show_all_gears")

    name = gear.name
    gear.delete()
    messages.success(request, f"🗑️ Gear '{name}' berhasil dihapus.")
    return redirect("gearguide:show_all_gears")


# ======================= AJAX HELPERS =======================
def _gear_to_json(gear: Gear):
    return {
        "id": str(gear.id),
        "sport_id": str(gear.sport.id) if gear.sport else None,
        "sport_name": gear.sport.name if gear.sport else "Unknown",
        "name": gear.name,
        "function": gear.function or "",
        "description": gear.description or "",
        "level": gear.level,
        "level_display": gear.get_level_display(),
        "price_range": gear.price_range or "",
        "recommended_brands": gear.recommended_brands or [],
        "materials": gear.materials or [],
        "care_tips": gear.care_tips or "",
        "ecommerce_link": gear.ecommerce_link or "",
        "tags": gear.tags or [],
        "image": gear.image or "",
    }


# ======================= AJAX GET =======================
@require_http_methods(["GET"])
def get_gear_json(request, gear_id):
    from uuid import UUID
    from pathlib import Path
    import json

    # 1️⃣ Ambil dari DB dulu
    try:
        try:
            gear = get_object_or_404(Gear, id=UUID(gear_id))
        except ValueError:
            gear = get_object_or_404(Gear, id=gear_id)

        data = {
            "id": str(gear.id),
            "name": gear.name,
            "function": gear.function,
            "description": gear.description,
            "level": gear.level,
            "price_range": gear.price_range,
            "recommended_brands": gear.recommended_brands or [],
            "materials": gear.materials or [],
            "care_tips": gear.care_tips,
            "buy_link": gear.buy_link,
            "tags": gear.tags or [],
            "image": gear.image.url if gear.image else "",
            "is_from_db": True,
        }
        return JsonResponse({"ok": True, "data": data}, status=200)

    except Exception:
        # 2️⃣ Fallback ke JSON file (kalau belum ada di DB)
        base_dir = Path(__file__).resolve().parent.parent.parent
        data_path = base_dir / 'database' / 'gears.json'
        if data_path.exists():
            with open(data_path, 'r', encoding='utf-8') as f:
                gears = json.load(f)
                gear = next((g for g in gears if str(g["id"]) == str(gear_id)), None)
                if gear:
                    return JsonResponse({"ok": True, "data": gear}, status=200)
        return JsonResponse({"ok": False, "error": "Gear tidak ditemukan."}, status=404)






# ======================= AJAX EDIT =======================
@login_required(login_url='login')
@require_http_methods(["POST"])
def edit_gear_ajax(request, gear_id):
    from uuid import UUID
    
    try:
        uuid_id = UUID(gear_id)
        gear = get_object_or_404(Gear, id=uuid_id)
        
        if hasattr(gear, "owner") and gear.owner != request.user:
            return JsonResponse({
                "ok": False,
                "message": "🚫 Kamu tidak punya izin untuk mengedit gear ini.",
                "errors": {"general": ["Kamu tidak punya izin untuk mengedit gear ini."]}
            }, status=403)
    except ValueError:
        return JsonResponse({
            "ok": False,
            "message": "❌ Gear dari JSON tidak bisa diedit.",
            "errors": {"general": ["Hanya gear yang dibuat user yang bisa diedit."]}
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "ok": False,
            "message": "❌ Gear tidak ditemukan.",
            "errors": {"general": [f"Gear tidak ditemukan: {str(e)}"]}
        }, status=404)

    form = GearForm(request.POST, instance=gear)
    if form.is_valid():
        try:
            gear = form.save(commit=False)
            
            # Handle sport conversion (sama kayak di add_gear)
            sport_value = form.cleaned_data.get("sport")
            if isinstance(sport_value, str):
                sport_obj = None
                try:
                    sport_uuid = UUID(sport_value)
                    sport_obj = Sport.objects.filter(id=sport_uuid).first()
                except ValueError:
                    pass

                if not sport_obj:
                    base_dir = Path(__file__).resolve().parent.parent.parent
                    sports_path = base_dir / "database" / "sports.json"
                    try:
                        with open(sports_path, "r", encoding="utf-8") as f:
                            sports_json = json.load(f)
                            sport_name = None
                            for s in sports_json:
                                if str(s["id"]) == str(sport_value):
                                    sport_name = s["name"]
                                    break
                            if sport_name:
                                sport_obj = Sport.objects.filter(name__iexact=sport_name).first()
                                if not sport_obj:
                                    sport_obj = Sport.objects.create(
                                        name=sport_name,
                                        category=s.get("category", "Umum"),
                                        difficulty=s.get("difficulty", "Menengah"),
                                        description=s.get("description", "Generated otomatis dari JSON."),
                                        history=s.get("history", "Tidak tersedia."),
                                    )
                    except Exception as e:
                        print(f"⚠️ Gagal membaca sports.json: {e}")

                gear.sport = sport_obj
            
            gear.save()
            updated = _gear_to_json(gear)
            return JsonResponse({
                "ok": True, 
                "message": f"✏️ Gear '{gear.name}' berhasil diperbarui!",
                "data": updated
            }, status=200)
        except Exception as e:
            return JsonResponse({
                "ok": False,
                "message": "❌ Gagal menyimpan gear.",
                "errors": {"general": [f"Gagal menyimpan: {str(e)}"]}
            }, status=500)

    errors_dict = {field: [str(err) for err in errs] for field, errs in form.errors.items()}
    return JsonResponse({
        "ok": False, 
        "message": "⚠️ Periksa kembali input kamu.",
        "errors": errors_dict
    }, status=400)

