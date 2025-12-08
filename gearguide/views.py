from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from uuid import UUID
import traceback
from django.urls import reverse
from metrics.utils import bump_view
from django.views.decorators.http import require_POST
from sportlibrary.models import Sport
from profile_app.models import ActivityLog
from .models import Gear

def admin_only(user):
    return user.is_staff or user.is_superuser


def _log_activity(request, gear_name):
    if request.user.is_authenticated:
        ActivityLog.objects.create(
            user=request.user,
            action_type="MODULE_ACCESS",
            description=f"Mengakses Gear: {gear_name}"
        )


def _gear_to_json(gear):
    return {
        "id": str(gear.id),
        "sport_id": str(gear.sport.id) if gear.sport else None,
        "sport_name": gear.sport.name if gear.sport else "Unknown",
        "name": gear.name,
        "function": gear.function or "",
        "description": gear.description or "",
        "level": gear.level,
        "level_display": gear.get_level_display() if hasattr(gear, "get_level_display") else gear.level,
        "price_range": gear.price_range or "",
        "recommended_brands": gear.recommended_brands or [],
        "materials": gear.materials or [],
        "care_tips": gear.care_tips or "",
        "ecommerce_link": gear.ecommerce_link or "",
        "tags": gear.tags or [],
        "image": gear.image or "",
        "owner": gear.owner.username if gear.owner else None,
    }

def show_all_gears(request):
    gears = Gear.objects.select_related("sport").all()
    all_sports = Sport.objects.all().order_by("name")

    # filter sport
    selected_sport = request.GET.get("sport", "").strip().lower()
    if selected_sport:
        gears = [g for g in gears if g.sport and g.sport.name.lower() == selected_sport]

    # filter level
    selected_level = request.GET.get("level", "").strip().lower()
    if selected_level:
        gears = [g for g in gears if g.level.lower() == selected_level]

    # filter: your gears
    view_filter = request.GET.get("view", "all")
    if view_filter == "your" and request.user.is_authenticated:
        gears = [g for g in gears if g.owner and g.owner.username == request.user.username]

    context = {
        "gears": gears,
        "all_sports": all_sports,
        "view_filter": view_filter,
        "title": "Gear Guide"
    }
    return render(request, "gearguide/gearguide.html", context)


def show_gear_detail(request, gear_id):
    """Tampilkan detail gear (langsung dari DB)"""
    try:
        gear = get_object_or_404(Gear, id=gear_id)
        _log_activity(request, gear.name)
        bump_view(
            key=f"gear:{gear.id}",
            title=gear.name,
            url=reverse('gearguide:card_details', kwargs={'gear_id': gear.id}),
            category="Gear",   
            image=(gear.image.url if getattr(gear, "image", None) and hasattr(gear.image, "url") else (gear.image or "")),
            request=request,
            dedupe_seconds=60, 
        )

        return render(request, "gearguide/card_details.html", {
            "gear": gear,
            "is_from_db": True
        })
    except Exception:
        raise Http404("Gear tidak ditemukan.")
    
@login_required(login_url="/accounts/login/")
def add_gear(request):
    """Tambah gear baru (user-generated)"""
    sports = Sport.objects.all()

    if request.method == "POST":
        try:
            name = request.POST.get("name")
            description = request.POST.get("description")
            sport_input = request.POST.get("sport")
            sport = None
            if sport_input:
                sport = Sport.objects.filter(id=sport_input).first() or \
                        Sport.objects.filter(name__iexact=sport_input).first()

            new_gear = Gear.objects.create(
                sport=sport,
                name=name,
                description=description,
                function=request.POST.get("function"),
                image=request.POST.get("image"),
                price_range=request.POST.get("price_range"),
                ecommerce_link=request.POST.get("ecommerce_link"),
                level=request.POST.get("level") or "beginner",
                recommended_brands=[b.strip() for b in request.POST.get("recommended_brands", "").split(",") if b.strip()],
                materials=[m.strip() for m in request.POST.get("materials", "").split(",") if m.strip()],
                care_tips=request.POST.get("care_tips"),
                tags=[t.strip() for t in request.POST.get("tags", "").split(",") if t.strip()],
                owner=request.user
            )

            ActivityLog.objects.create(
                user=request.user,
                action_type="CREATE",
                description=f"User '{request.user.username}' menambahkan gear '{new_gear.name}'"
            )
            messages.success(request, f"✅ Gear '{new_gear.name}' berhasil ditambahkan!")
            return redirect("gearguide:show_all_gears")

        except Exception as e:
            traceback.print_exc()
            messages.error(request, f"❌ Gagal menambahkan gear: {e}")

    return render(request, "gear_app/gear_form.html", {"sports": sports, "edit_mode": False})


@login_required
def edit_gear(request, gear_id):
    """Edit gear (hanya admin atau pemilik)"""
    gear = get_object_or_404(Gear, id=gear_id)

    if not (request.user.is_staff or request.user.is_superuser or gear.owner == request.user):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "message": "❌ Hanya admin atau pemilik gear yang dapat mengedit gear ini."}, status=403)
        return HttpResponseForbidden("❌ Kamu tidak punya izin untuk mengedit gear ini.")

    if request.method == "POST":
        try:
            sport_id = request.POST.get("sport")
            sport = Sport.objects.filter(id=sport_id).first() if sport_id else None

            gear.name = request.POST.get("name")
            gear.description = request.POST.get("description")
            gear.function = request.POST.get("function")
            gear.sport = sport
            gear.image = request.POST.get("image")
            gear.price_range = request.POST.get("price_range")
            gear.ecommerce_link = request.POST.get("ecommerce_link")
            gear.level = request.POST.get("level")
            gear.recommended_brands = [b.strip() for b in request.POST.get("recommended_brands", "").split(",") if b.strip()]
            gear.materials = [m.strip() for m in request.POST.get("materials", "").split(",") if m.strip()]
            gear.care_tips = request.POST.get("care_tips")
            gear.tags = [t.strip() for t in request.POST.get("tags", "").split(",") if t.strip()]
            gear.save()

            ActivityLog.objects.create(
                user=request.user,
                action_type="UPDATE",
                description=f"User '{request.user.username}' mengedit gear '{gear.name}'"
            )
            return JsonResponse({"ok": True, "message": "✅ Gear berhasil diperbarui!"})

        except Exception as e:
            return JsonResponse({"ok": False, "message": f"❌ Gagal memperbarui gear: {e}"}, status=400)

    return JsonResponse({"ok": False, "message": "❌ Metode tidak valid."}, status=405)


@login_required
@csrf_exempt
def delete_gear(request, gear_id):
    """Hapus gear (hanya admin/superuser)"""
    gear = get_object_or_404(Gear, id=gear_id)

    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({"ok": False, "message": "❌ Hanya admin yang dapat menghapus gear."}, status=403)

    if request.method == "POST":
        gear_name = gear.name
        gear.delete()

        ActivityLog.objects.create(
            user=request.user,
            action_type="DELETE",
            description=f"Admin '{request.user.username}' menghapus gear '{gear_name}'"
        )

        return JsonResponse({"ok": True, "message": f"🗑️ Gear '{gear_name}' berhasil dihapus!"})

    return JsonResponse({"ok": False, "message": "❌ Metode tidak valid."}, status=405)

@require_http_methods(["GET"])
def get_gear_json(request, gear_id):
    """Endpoint buat ambil data gear via AJAX"""
    try:
        gear = Gear.objects.filter(id=gear_id).first()
        if not gear:
            return JsonResponse({"ok": False, "error": "Gear tidak ditemukan."}, status=404)

        data = _gear_to_json(gear)
        data.update({
            "recommended_brands_text": ", ".join(data["recommended_brands"]),
            "materials_text": ", ".join(data["materials"]),
            "tags_text": ", ".join(data["tags"]),
        })
        return JsonResponse({"ok": True, "data": data}, status=200)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
    

def get_all_gears_json(request):
    gears = Gear.objects.select_related('sport').all()

    data = []
    for g in gears:
        data.append({
            "id": str(g.id),
            "sport_id": str(g.sport.id) if g.sport else None,
            "sport_name": g.sport.name if g.sport else None,
            "name": g.name,
            "function": g.function,
            "description": g.description,
            "level": g.level,  # 'beginner' / 'intermediate' / 'advanced'
            "level_display": g.get_level_display(),  # 'Pemula', 'Menengah', 'Lanjutan'
            "price_range": g.price_range,
            "recommended_brands": g.recommended_brands or [],
            "materials": g.materials or [],
            "care_tips": g.care_tips,
            "ecommerce_link": g.ecommerce_link,
            "tags": g.tags or [],
            "image": g.image,
            "owner": g.owner.username if g.owner else None,
        })

    response = {
        "ok": True,
        "count": len(data),
        "data": data,
    }
    return JsonResponse(response)
    

@csrf_exempt
@require_POST
@login_required(login_url="/accounts/login/")
def add_gear_flutter(request):
    try:
        data = json.loads(request.body.decode("utf-8"))

        sport = None
        sport_input = data.get("sport")
        if sport_input:
            sport = Sport.objects.filter(id=sport_input).first() or \
                    Sport.objects.filter(name__iexact=sport_input).first()

        new_gear = Gear.objects.create(
            sport=sport,
            name=data.get("name"),
            description=data.get("description"),
            function=data.get("function"),
            image=data.get("image"),
            price_range=data.get("price_range"),
            ecommerce_link=data.get("ecommerce_link"),
            level=data.get("level") or "beginner",
            recommended_brands=[b.strip() for b in data.get("recommended_brands", []) if b.strip()],
            materials=[m.strip() for m in data.get("materials", []) if m.strip()],
            care_tips=data.get("care_tips"),
            tags=[t.strip() for t in data.get("tags", []) if t.strip()],
            owner=request.user,
        )

        return JsonResponse({
            "ok": True,
            "message": "Gear berhasil dibuat dari Flutter",
            "data": _gear_to_json(new_gear),
        }, status=201)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

