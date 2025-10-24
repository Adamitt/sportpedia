from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.urls import reverse
from uuid import UUID
import json
import traceback
from pathlib import Path
from django.http import Http404
from django.views.decorators.csrf import csrf_exempt

from metrics.utils import bump_view
from sportlibrary.models import Sport
from profile_app.models import ActivityLog
from .models import Gear


def admin_only(user):
    """Hanya admin/staff yang lolos"""
    return user.is_staff or user.is_superuser


def _log_activity(request, gear_name):
    """Log user activity if authenticated"""
    if request.user.is_authenticated:
        ActivityLog.objects.create(
            user=request.user,
            action_type="MODULE_ACCESS",
            description=f"Mengakses Gear: {gear_name}"
        )


def _gear_to_json(gear):
    """Convert Gear model ke JSON-serializable dict"""
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

def show_gear_detail(request, gear_id):
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_path = base_dir / 'database' / 'gears.json'

    key = f"gear:{gear.id}"
    url = reverse("gearguide:card_details", kwargs={"gear_id": str(gear.id)})
    bump_view(
        key,
        title=gear.name,
        url=url,
        category="Gear",
        image=(gear.image or ""),
        request=request,
    )
    # 1️⃣ Coba cari di database (UUID)
    try:
        gear = Gear.objects.get(id=gear_id)
        return render(request, 'gearguide/card_details.html', {'gear': gear, 'is_from_db': True})
    except Gear.DoesNotExist:
        pass

    # 2️⃣ Kalau gak ketemu, cari di JSON file
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            gears = json.load(f)
            for g in gears:
                if str(g.get("id")) == str(gear_id):
                    return render(request, 'gearguide/card_details.html', {'gear': g, 'is_from_db': False})

    # 3️⃣ Kalau gak ada di dua-duanya, raise 404
    raise Http404("Gear not found.")


def show_all_gears(request):
    base = settings.BASE_DIR
    gears_path = base / "database" / "gears.json"
    sports_path = base / "database" / "sports.json"

    json_gears, json_sports = [], []
    if gears_path.exists():
        with open(gears_path, "r", encoding="utf-8") as f:
            json_gears = json.load(f)
    if sports_path.exists():
        with open(sports_path, "r", encoding="utf-8") as f:
            json_sports = json.load(f)

    sport_map = {str(s["id"]): s["name"] for s in json_sports}
    combined_gears = []

    # ===== Dari JSON =====
    for g in json_gears:
        sport_id = str(g.get("sport_id", ""))
        combined_gears.append({
            "id": g.get("id"),
            "sport": sport_map.get(sport_id, g.get("sport", "Unknown")),
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

    # ===== Dari DB =====
    for g in Gear.objects.select_related("sport").all():
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
            "owner": g.owner.username if g.owner else None,
        })

    # ========== FILTER berdasarkan parameter GET ==========
    selected_sport = request.GET.get("sport", "").strip().lower()
    selected_level = request.GET.get("level", "").strip()

    if selected_sport:
        combined_gears = [
            g for g in combined_gears if g["sport"].lower() == selected_sport
        ]

    if selected_level:
        combined_gears = [
            g for g in combined_gears if g["level"].lower() == selected_level.lower()
        ]

    # ========== Filter view (your/all) ==========
    view_filter = request.GET.get("view", "all")
    if view_filter == "your" and request.user.is_authenticated:
        combined_gears = [g for g in combined_gears if g.get("owner") == request.user.username]

    all_sports_list = json_sports

    return render(request, "gearguide/gearguide.html", {
        "gears": combined_gears,
        "all_sports": all_sports_list,
        "view_filter": view_filter,
        "title": "Gear Guide"
    })



@login_required(login_url="/accounts/login/")
def add_gear(request):
    sports = Sport.objects.all()

    if request.method == "POST":
        try:
            name = request.POST.get("name")
            description = request.POST.get("description")
            sport_input = request.POST.get("sport")

            # 🧩 Coba cari sport berdasarkan ID atau nama
            sport = None
            if sport_input:
                sport = Sport.objects.filter(id=sport_input).first()
                if not sport:
                    sport = Sport.objects.filter(name__iexact=sport_input).first()

            function = request.POST.get("function")
            image = request.POST.get("image")
            price_range = request.POST.get("price_range")
            ecommerce_link = request.POST.get("ecommerce_link")
            level = request.POST.get("level") or "beginner"
            recommended_brands = [b.strip() for b in request.POST.get("recommended_brands", "").split(",") if b.strip()]
            materials = [m.strip() for m in request.POST.get("materials", "").split(",") if m.strip()]
            care_tips = request.POST.get("care_tips")
            tags = [t.strip() for t in request.POST.get("tags", "").split(",") if t.strip()]

            # 🛠️ Buat gear baru (siapa pun boleh)
            new_gear = Gear.objects.create(
            sport=sport,
            name=name,
            description=description,
            function=function,
            image=image,
            price_range=price_range,
            ecommerce_link=ecommerce_link,
            level=level,
            recommended_brands=recommended_brands,
            materials=materials,
            care_tips=care_tips,
            tags=tags,
            owner=request.user,  # ✅ HARUS USER IANSTANCE
            )
            

            # 📝 Log aktivitas
            ActivityLog.objects.create(
                user=request.user,
                action_type="CREATE",
                description=f"User '{request.user.username}' menambahkan gear '{new_gear.name}'"
            )

            messages.success(request, "✅ Gear berhasil ditambahkan!")
            return redirect("gearguide:show_all_gears")

        except Exception as e:
            traceback.print_exc()
            messages.error(request, f"❌ Gagal menambahkan gear: {e}")

    return render(request, "gear_app/gear_form.html", {"sports": sports, "edit_mode": False})



from django.http import JsonResponse, HttpResponseForbidden

@login_required
def edit_gear(request, gear_id):
    gear = get_object_or_404(Gear, id=gear_id)

    # 🧠 Cek hak akses
    if not (request.user.is_staff or request.user.is_superuser or gear.owner == request.user.username):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "message": "❌ Hanya admin atau pemilik gear yang dapat mengedit gear ini."}, status=403)
        return HttpResponseForbidden("❌ Kamu tidak punya izin untuk mengedit gear ini.")

    if request.method == 'POST':
        try:
            gear.name = request.POST.get('name')
            gear.description = request.POST.get('description')
            gear.function = request.POST.get('function')
            sport_id = request.POST.get('sport')
            if sport_id:
                gear.sport = Sport.objects.get(id=sport_id)
            gear.image = request.POST.get('image')
            gear.price_range = request.POST.get('price_range')
            gear.ecommerce_link = request.POST.get('ecommerce_link')
            gear.level = request.POST.get('level')
            gear.recommended_brands = [b.strip() for b in request.POST.get('recommended_brands', '').split(',') if b.strip()]
            gear.materials = [m.strip() for m in request.POST.get('materials', '').split(',') if m.strip()]
            gear.care_tips = request.POST.get('care_tips')
            gear.tags = [t.strip() for t in request.POST.get('tags', '').split(',') if t.strip()]
            gear.save()
            return JsonResponse({"ok": True, "message": "✅ Gear berhasil diperbarui!"})
        except Exception as e:
            return JsonResponse({"ok": False, "message": f"❌ Gagal memperbarui gear: {e}"}, status=400)

    return JsonResponse({"ok": False, "message": "❌ Metode tidak valid."}, status=405)



@login_required
@csrf_exempt  # biar request fetch tanpa form masih diterima
def delete_gear(request, gear_id):
    gear = get_object_or_404(Gear, id=gear_id)

    # ❌ Kalau bukan admin/superuser
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({
            "ok": False,
            "message": "❌ Hanya admin yang dapat menghapus gear."
        }, status=403)

    # ✅ Kalau admin
    if request.method == "POST":
        gear_name = gear.name
        gear.delete()
        return JsonResponse({
            "ok": True,
            "message": f"🗑️ Gear '{gear_name}' berhasil dihapus!"
        })

    return JsonResponse({
        "ok": False,
        "message": "❌ Metode tidak valid."
    }, status=405)


@require_http_methods(["GET"])
def get_gear_json(request, gear_id):
    try:
        gear = Gear.objects.filter(id=gear_id).first()
        if not gear:
            with open(settings.BASE_DIR / "database" / "gears.json", "r", encoding="utf-8") as f:
                gears = json.load(f)
                gear = next((g for g in gears if str(g["id"]) == str(gear_id)), None)
                if not gear:
                    return JsonResponse({"ok": False, "error": "Gear tidak ditemukan."}, status=404)
                return JsonResponse({"ok": True, "data": gear}, status=200)

        data = _gear_to_json(gear)
        data.update({
            "recommended_brands_text": ", ".join(data["recommended_brands"]),
            "materials_text": ", ".join(data["materials"]),
            "tags_text": ", ".join(data["tags"]),
        })
        return JsonResponse({"ok": True, "data": data}, status=200)

    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({"ok": False, "error": str(e)}, status=500)