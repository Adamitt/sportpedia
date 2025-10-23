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

def show_gear_detail(request, gear_id):
    gear = get_object_or_404(Gear, id=gear_id)
    context = {
        "title": gear.name,
        "gear": gear,
    }
    return render(request, "gearguide/gear_detail.html", context)

def show_all_gears(request):
    db_gears = list(Gear.objects.all().select_related('sport'))

    base_dir = Path(__file__).resolve().parent.parent.parent
    data_path = base_dir / 'database' / 'gears.json'
    with open(data_path, 'r', encoding='utf-8') as file:
        json_gears = json.load(file)

    combined_gears = []

    # JSON items
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
        })

    # DB items
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
        })

    # 🔹 Ambil filter dari query
    sport_filter = request.GET.get('sport')
    level_filter = request.GET.get('level')
    source_filter = request.GET.get('source')  # 🆕 "db" / "json" / "all"

    # Filter jenis sport
    if sport_filter:
        combined_gears = [
            g for g in combined_gears
            if sport_filter.lower() in str(g["sport"]).lower()
        ]

    # Filter level
    if level_filter:
        combined_gears = [
            g for g in combined_gears
            if g.get("level", "").lower() == level_filter.lower()
        ]

    # 🔹 Filter sumber data
    if source_filter == "db":
        combined_gears = [g for g in combined_gears if g["is_from_db"]]
    elif source_filter == "json":
        combined_gears = [g for g in combined_gears if not g["is_from_db"]]

    sports = sorted(set(str(g["sport"]) for g in combined_gears if g.get("sport")))
    all_sports = Sport.objects.all().order_by('name')

    return render(request, "gearguide/gearguide.html", {
        "title": "Gear Guide",
        "gears": combined_gears,
        "sports": sports,
        "all_sports": all_sports,
        "source_filter": source_filter or "all",  # 🔹 kirim ke template
    })


def card_details(request, gear_id):
    """
    Tampilkan detail gear.
    1) Coba cari di DB (UUID)
    2) Kalau tidak ada, cek di JSON
    """
    # 1) Coba treat sebagai UUID dan cari di DB
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
            return render(request, "gearguide/card_details.html", context)
    except ValueError:
        # bukan UUID, langsung ke JSON
        pass

    # 2) Cek JSON
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_path = base_dir / 'database' / 'gears.json'
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

    context = {"title": gear["name"], "gear": gear}
    return render(request, "gearguide/card_details.html", context)

def add_gear(request):
    if request.method == "POST":
        form = GearForm(request.POST)
        if form.is_valid():
            gear = form.save(commit=False)
            if request.user.is_authenticated:
                gear.owner = request.user  # 🆕 simpan user yang login
            gear.save()
            messages.success(request, "✅ Gear baru berhasil ditambahkan!")
            return redirect("gearguide:show_all_gears")
    else:
        form = GearForm()

    return render(request, "gearguide/add_gear.html", {"form": form})

def delete_gear(request, gear_id):
    """
    Hanya hapus gear dari database.
    Gear dari JSON tidak bisa dihapus.
    """
    try:
        gear = get_object_or_404(Gear, id=gear_id)
        name = gear.name
        gear.delete()
        messages.success(request, f"🗑 Gear '{name}' berhasil dihapus dari database.")
    except Exception as e:
        messages.error(request, f"❌ Gagal menghapus gear: {str(e)}")

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

@require_http_methods(["POST"])
def edit_gear_ajax(request, gear_id):
    """
    AJAX POST: update gear via forms.py (ModelForm).
    """
    try:
        gear = get_object_or_404(Gear, id=gear_id)
    except Exception as e:
        return JsonResponse({
            "ok": False,
            "errors": {"general": [f"Gear tidak ditemukan: {str(e)}"]}
        }, status=404)

    # Gunakan GearForm supaya clean_* untuk list jalan
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

    # Kirim error field-friendly
    errors_dict = {}
    for field, errs in form.errors.items():
        errors_dict[field] = [str(err) for err in errs]
    
    return JsonResponse({
        "ok": False,
        "errors": errors_dict
    }, status=400)

