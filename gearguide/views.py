from django.urls import reverse
from metrics.utils import bump_view
from django.conf import settings
import json
from uuid import UUID
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Gear
from .forms import GearForm
from sportlibrary.models import Sport
from django.contrib.auth.decorators import login_required
from profile_app.models import ActivityLog
import traceback


# ======================= HELPER FUNCTIONS =======================
def _get_or_create_sport(sport_value):
    """Helper untuk mendapatkan atau membuat Sport object dari string ID"""
    # 1️⃣ Coba parse sebagai UUID (dari DB)
    try:
        sport_uuid = UUID(sport_value)
        sport_obj = Sport.objects.filter(id=sport_uuid).first()
        if sport_obj:
            return sport_obj
    except (ValueError, AttributeError):
        pass

    # 2️⃣ Cari di JSON berdasarkan ID
    sports_path = settings.BASE_DIR / "database" / "sports.json"
    if sports_path.exists():
        try:
            with open(sports_path, "r", encoding="utf-8") as f:
                sports_json = json.load(f)
                for s in sports_json:
                    if str(s["id"]) == str(sport_value):
                        # Cari di DB berdasarkan nama
                        sport_obj = Sport.objects.filter(name__iexact=s["name"]).first()
                        if not sport_obj:
                            # Buat baru otomatis
                            sport_obj = Sport.objects.create(
                                name=s["name"],
                                category=s.get("category", "Umum"),
                                difficulty=s.get("difficulty", "Menengah"),
                                description=s.get("description", "Generated otomatis dari JSON."),
                                history=s.get("history", "Tidak tersedia."),
                            )
                        return sport_obj
        except Exception as e:
            print(f"⚠️ Gagal membaca sports.json: {e}")

    return None


def _gear_to_json(gear):
    """Convert Gear model to JSON-serializable dict"""
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
        "buy_link": gear.ecommerce_link or "",
        "tags": gear.tags or [],
        "image": gear.image or "",
    }


def _log_activity(request, gear_name):
    """Log user activity if authenticated"""
    if request.user.is_authenticated:
        ActivityLog.objects.create(
            user=request.user,
            action_type="MODULE_ACCESS",
            description=f"Mengakses Gear: {gear_name}"
        )


# ======================= DETAIL VIEW =======================
def show_gear_detail(request, gear_id):
    gear = get_object_or_404(Gear, id=gear_id)

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

    _log_activity(request, gear.name)

    context = {
        "title": gear.name,
        "gear": gear,
    }
    return render(request, "gearguide/gear_detail.html", context)


# ======================= SHOW ALL GEARS =======================
def show_all_gears(request):
    BASE_DIR = settings.BASE_DIR
    gears_path = BASE_DIR / 'database' / 'gears.json'
    sports_path = BASE_DIR / 'database' / 'sports.json'

    # Load sports dari JSON
    json_sports = []
    if sports_path.exists():
        with open(sports_path, 'r', encoding='utf-8') as file:
            json_sports = json.load(file)

    # Map sport_id ke nama sport
    sport_map = {str(s['id']): s['name'] for s in json_sports}

    # Load gears dari JSON
    json_gears = []
    if gears_path.exists():
        with open(gears_path, 'r', encoding='utf-8') as file:
            json_gears = json.load(file)

    # Load Gear dari DB
    db_gears = list(Gear.objects.select_related('sport').all())
    combined_gears = []

    # Gabungkan JSON ITEMS
    for g in json_gears:
        sport_id = str(g.get("sport_id", ""))
        sport_name = sport_map.get(sport_id, g.get("sport", "Unknown"))

        combined_gears.append({
            "id": g.get("id"),
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

    # Gabungkan DB ITEMS
    for g in db_gears:
        combined_gears.append({
            "id": str(g.id),
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
            "owner": g.owner.username if hasattr(g, "owner") and g.owner else None,
        })

    # FILTER LOGIC
    sport_filter = request.GET.get('sport', '').strip()
    level_filter = request.GET.get('level', '').strip()
    view_filter = request.GET.get('view', 'all')

    if sport_filter:
        combined_gears = [
            g for g in combined_gears
            if g.get("sport", "").lower() == sport_filter.lower()
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

    # Dropdown sports
    sports = sorted(set(s['name'] for s in json_sports if s.get('name')))

    # all_sports untuk modal edit
    all_sports_list = []
    
    for sport in Sport.objects.all():
        all_sports_list.append({
            'id': str(sport.id),
            'name': sport.name
        })
    
    db_sport_names = [s['name'].lower() for s in all_sports_list]
    for s in json_sports:
        if s['name'].lower() not in db_sport_names:
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
def card_details(request, gear_id):
    # Coba cari dulu di DB
    gear = Gear.objects.filter(id=gear_id).first()
    
    if gear:
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

        _log_activity(request, gear.name)

        return render(request, "gearguide/card_details.html", {
            "title": gear.name,
            "gear": gear,
        })

    # Fallback ke JSON
    data_path = settings.BASE_DIR / 'database' / 'gears.json'
    if not data_path.exists():
        return render(request, "404.html", status=404)

    with open(data_path, 'r', encoding='utf-8') as file:
        gears = json.load(file)
        gear = next((g for g in gears if str(g['id']) == str(gear_id)), None)

    if not gear:
        return render(request, "404.html", status=404)

    sport_name = gear.get("sport", "Unknown")
    sport_id = gear.get("sport_id")
    if sport_id:
        sport_obj = Sport.objects.filter(id=sport_id).first()
        if sport_obj:
            sport_name = sport_obj.name

    gear["sport"] = sport_name
    gear["is_from_db"] = False

    key = f"gearjson:{gear['id']}"
    url = reverse("gearguide:card_details", kwargs={"gear_id": str(gear['id'])})
    bump_view(
        key,
        title=gear["name"],
        url=url,
        category="Gear Guide",
        image=gear.get("image", ""),
        request=request,
    )

    _log_activity(request, gear.get("name", "Unknown"))

    return render(request, "gearguide/card_details.html", {
        "title": gear["name"],
        "gear": gear,
    })


# ======================= ADD GEAR =======================
@login_required(login_url='login')
def add_gear(request):
    if request.method == "POST":
        form = GearForm(request.POST)
        if form.is_valid():
            gear = form.save(commit=False)

            sport_value = form.cleaned_data.get("sport")
            if isinstance(sport_value, str):
                gear.sport = _get_or_create_sport(sport_value)
            else:
                gear.sport = sport_value

            gear.owner = request.user
            gear.save()
            form.save_m2m()

            messages.success(request, f"✅ Gear '{gear.name}' berhasil ditambahkan!")
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

    if gear.owner and gear.owner != request.user:
        messages.error(request, "🚫 Kamu tidak punya izin untuk menghapus gear ini.")
        return redirect("gearguide:show_all_gears")

    name = gear.name
    gear.delete()
    messages.success(request, f"🗑️ Gear '{name}' berhasil dihapus.")
    return redirect("gearguide:show_all_gears")


# ======================= AJAX GET =======================
@require_http_methods(["GET"])
def get_gear_json(request, gear_id):
    # Coba cari di DB
    gear = Gear.objects.filter(id=gear_id).first()
    
    if not gear:
        try:
            uuid_id = UUID(str(gear_id))
            gear = Gear.objects.filter(id=uuid_id).first()
        except (ValueError, AttributeError):
            pass

    # Kalau ketemu di DB
    if gear:
        data = _gear_to_json(gear)
        data.update({
            "recommended_brands_text": ", ".join(data["recommended_brands"]),
            "materials_text": ", ".join(data["materials"]),
            "tags_text": ", ".join(data["tags"]),
        })
        return JsonResponse({"ok": True, "data": data}, status=200)

    # Fallback ke JSON file
    data_path = settings.BASE_DIR / "database" / "gears.json"
    if data_path.exists():
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                gears = json.load(f)
                gear = next((g for g in gears if str(g["id"]) == str(gear_id)), None)
                if gear:
                    return JsonResponse({"ok": True, "data": gear}, status=200)
        except Exception as e:
            print(f"⚠️ Error reading gears.json: {e}")

    return JsonResponse({"ok": False, "error": "Gear tidak ditemukan."}, status=404)


# ======================= AJAX EDIT =======================
@login_required(login_url='login')
@require_http_methods(["POST"])
def edit_gear_ajax(request, gear_id):
    """
    AJAX endpoint untuk edit gear.
    HARUS return JSON dalam semua kondisi.
    """
    
    # Debug logging
    print("\n" + "="*60)
    print("🔧 EDIT GEAR AJAX CALLED")
    print("="*60)
    print(f"📌 Gear ID: {gear_id}")
    print(f"👤 User: {request.user.username}")
    print(f"📨 Method: {request.method}")
    print(f"🔐 Is AJAX: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
    print(f"📋 POST data: {dict(request.POST)}")
    print("="*60 + "\n")
    
    try:
        # 1️⃣ Coba ambil gear di DB
        gear = Gear.objects.filter(id=gear_id).first()
        
        if not gear:
            try:
                uuid_id = UUID(str(gear_id))
                gear = Gear.objects.filter(id=uuid_id).first()
            except (ValueError, AttributeError) as e:
                print(f"⚠️ UUID conversion error: {e}")

        if not gear:
            print("❌ Gear not found")
            return JsonResponse({
                "ok": False,
                "message": "❌ Gear tidak ditemukan atau merupakan gear bawaan sistem.",
            }, status=404)

        print(f"✅ Gear found: {gear.name}")

        # 2️⃣ Cek kepemilikan
        if gear.owner and gear.owner != request.user:
            print(f"🚫 Permission denied: {request.user.username} != {gear.owner.username}")
            return JsonResponse({
                "ok": False,
                "message": "🚫 Kamu tidak punya izin untuk mengedit gear ini.",
            }, status=403)

        print("✅ Permission check passed")

        # 3️⃣ Validasi dan simpan
        form = GearForm(request.POST, instance=gear)
        
        if form.is_valid():
            print("✅ Form valid")
            
            # Handle sport conversion
            sport_value = form.cleaned_data.get("sport")
            if isinstance(sport_value, str):
                gear.sport = _get_or_create_sport(sport_value)
            else:
                gear.sport = sport_value

            gear = form.save()
            print(f"✅ Gear saved: {gear.name}")

            # Convert to JSON
            updated = _gear_to_json(gear)

            return JsonResponse({
                "ok": True,
                "message": f"✏️ Gear '{gear.name}' berhasil diperbarui!",
                "data": updated
            }, status=200)
        else:
            print("⚠️ Form invalid:")
            print(form.errors.as_json())
            
            errors_dict = {
                field: [str(err) for err in errs] 
                for field, errs in form.errors.items()
            }
            return JsonResponse({
                "ok": False,
                "message": "⚠️ Periksa kembali input kamu.",
                "errors": errors_dict
            }, status=400)
            
    except Exception as e:
        print("💥 EXCEPTION OCCURRED:")
        print(traceback.format_exc())
        
        return JsonResponse({
            "ok": False,
            "message": f"❌ Terjadi kesalahan server: {str(e)}",
            "error": str(e)
        }, status=500)