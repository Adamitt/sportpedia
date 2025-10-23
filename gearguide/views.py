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

def show_all_gears(request):
    db_gears = list(Gear.objects.select_related('sport').all())

    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    data_path = BASE_DIR / 'database' / 'gears.json'

    json_gears = []
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as file:
            json_gears = json.load(file)
    # 2️⃣ Ambil dari JSON
    data_path = settings.BASE_DIR / 'database' / 'gears.json'
    with open(data_path, 'r', encoding='utf-8') as file:
        json_gears = json.load(file)

    combined_gears = []

    # === JSON ITEMS ===
    for g in json_gears:
        sport_name = "Unknown"
        sport_id = g.get("sport_id")
        if sport_id:
            try:
                sport_obj = Sport.objects.get(id=sport_id)
                sport_name = sport_obj.name
            except Sport.DoesNotExist:
                sport_name = g.get("sport", "Unknown")
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

    # === DB ITEMS ===
    for g in db_gears:
        combined_gears.append({
            "id": g.id,
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

    # === FILTER LOGIC ===
    sport_filter = request.GET.get('sport')
    level_filter = request.GET.get('level')
    view_filter = request.GET.get('view', 'all')  # new filter (all / your)

    # Sport filter
    if sport_filter:
        combined_gears = [g for g in combined_gears if sport_filter.lower() in str(g["sport"]).lower()]

    # Level filter
    if level_filter:
        combined_gears = [g for g in combined_gears if g.get("level", "").lower() == level_filter.lower()]

    # === View filter (new) ===
    if view_filter == "your":
        if request.user.is_authenticated:
            combined_gears = [
                g for g in combined_gears
                if g["is_from_db"] and g.get("owner") == request.user.username
            ]
        else:
            combined_gears = []  # ga login = kosong
    elif view_filter == "all":
        combined_gears = combined_gears  # keep everything (JSON + DB)

    sports = sorted(set(str(g["sport"]) for g in combined_gears if g.get("sport")))
    all_sports = Sport.objects.all().order_by('name')

    return render(request, "gearguide/gearguide.html", {
        "title": "Gear Guide",
        "gears": combined_gears,
        "sports": sports,
        "all_sports": all_sports,
        "view_filter": view_filter,
    })

def card_details(request, gear_id):
    try:
        _ = UUID(str(gear_id))
        gear = Gear.objects.select_related('sport').filter(id=gear_id).first()
        if gear:
            context = {
                "title": gear.name,
                "gear": {
                    "id": str(gear.id),
                    "sport": gear.sport.name if gear.sport else "Unknown",
                    "name": gear.name,
                    "function": gear.function,
                    "description": gear.description,
                    "level": gear.get_level_display(),
                    "price_range": gear.price_range,
                    "recommended_brands": gear.recommended_brands or [],
                    "materials": gear.materials or [],
                    "care_tips": gear.care_tips,
                    "buy_link": gear.ecommerce_link,
                    "tags": gear.tags or [],
                    "image": gear.image or "",
                    "is_from_db": True
                }
            }

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

            return render(request, "gearguide/card_details.html", context)
    except ValueError:
        pass

    base_dir = Path(__file__).resolve().parent.parent.parent
    data_path = base_dir / 'database' / 'gears.json'
    # 2) Cek JSON
    data_path = settings.BASE_DIR / 'database' / 'gears.json'     
    with open(data_path, 'r', encoding='utf-8') as file:
        gears = json.load(file)

    gear = next((g for g in gears if str(g['id']) == str(gear_id)), None)
    if not gear:
        return render(request, "404.html", status=404)
    

    # ⭐ Ambil nama sport dari database berdasarkan sport_id
    sport_name = "Unknown"
    sport_id = gear.get("sport_id")
    if sport_id:
        try:
            sport_obj = Sport.objects.get(id=sport_id)
            sport_name = sport_obj.name
        except Sport.DoesNotExist:
            sport_name = gear.get("sport", "Unknown")
    else:
        sport_name = gear.get("sport", "Unknown")

    gear['is_from_db'] = False
    gear['sport'] = sport_name

    # ✅ catat view (gear dari JSON)
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

    context = {"title": gear["name"], "gear": gear}
    return render(request, "gearguide/card_details.html", context)

@login_required(login_url='login')
def add_gear(request):
    if request.method == "POST":
        form = GearForm(request.POST)
        if form.is_valid():
            gear = form.save(commit=False)
            gear.owner = request.user
            gear.save()
            return redirect("gearguide:show_all_gears")
    else:
        form = GearForm()
    return render(request, "gearguide/add_gear.html", {"form": form})

@login_required(login_url='login')
@require_http_methods(["POST"])
def delete_gear(request, gear_id):
    gear = get_object_or_404(Gear, id=gear_id)
    if hasattr(gear, "owner") and gear.owner != request.user:
        return redirect("gearguide:show_all_gears")

    name = gear.name
    gear.delete()
    messages.success(request, f"🗑 Gear '{name}' berhasil dihapus.")
    return redirect("gearguide:show_all_gears")

# ============ AJAX FUNCTIONS ============

def _gear_to_json(gear: Gear):
    """Helper function untuk convert Gear model ke JSON"""
    return {
        "id": str(gear.id),
        "sport_id": str(gear.sport.id) if gear.sport else None,
        "sport_name": gear.sport.name if gear.sport else "Unknown",
        "name": gear.name,
        "function": gear.function or "",
        "description": gear.description or "",
        "level": gear.level,  # Return code, bukan display
        "level_display": gear.get_level_display(),
        "price_range": gear.price_range or "",
        "recommended_brands": gear.recommended_brands or [],
        "materials": gear.materials or [],
        "care_tips": gear.care_tips or "",
        "ecommerce_link": gear.ecommerce_link or "",
        "tags": gear.tags or [],
        "image": gear.image or "",
    }

@require_http_methods(["GET"])
def get_gear_json(request, gear_id):
    """
    AJAX GET: detail gear dari DB (bukan JSON file).
    """
    try:
        gear = get_object_or_404(Gear, id=gear_id)
    except Exception:
        return JsonResponse({"ok": False, "error": "Gear tidak ditemukan di database."}, status=404)

    data = _gear_to_json(gear)
    # Untuk prefill form text (comma separated)
    data.update({
        "recommended_brands_text": ", ".join(data["recommended_brands"]),
        "materials_text": ", ".join(data["materials"]),
        "tags_text": ", ".join(data["tags"]),
    })
    return JsonResponse({"ok": True, "data": data}, status=200)

@login_required(login_url='login')
@require_http_methods(["POST"])
def edit_gear_ajax(request, gear_id):
    try:
        gear = get_object_or_404(Gear, id=gear_id)
        if hasattr(gear, "owner") and gear.owner != request.user:
            return JsonResponse({
                "ok": False,
                "errors": {"general": ["Kamu tidak punya izin untuk mengedit gear ini."]}
            }, status=403)
    except Exception as e:
        return JsonResponse({
            "ok": False,
            "errors": {"general": [f"Gear tidak ditemukan: {str(e)}"]}
        }, status=404)

    form = GearForm(request.POST, instance=gear)
    if form.is_valid():
        try:
            gear = form.save()
            updated = _gear_to_json(gear)
            return JsonResponse({"ok": True, "data": updated}, status=200)
        except Exception as e:
            return JsonResponse({
                "ok": False,
                "errors": {"general": [f"Gagal menyimpan: {str(e)}"]}
            }, status=500)

    errors_dict = {field: [str(err) for err in errs] for field, errs in form.errors.items()}
    return JsonResponse({"ok": False, "errors": errors_dict}, status=400)