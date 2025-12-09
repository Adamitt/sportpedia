from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

import json
import traceback

from metrics.utils import bump_view
from sportlibrary.models import Sport
from profile_app.models import ActivityLog
from .models import Gear


# =========================
# Helper functions
# =========================

def admin_only(user):
    """Return True kalau user adalah staff/superuser (admin)."""
    return user.is_staff or user.is_superuser


def _log_activity(request, gear_name):
    """Catat log aktivitas kalau user login."""
    if request.user.is_authenticated:
        ActivityLog.objects.create(
            user=request.user,
            action_type="MODULE_ACCESS",
            description=f"Mengakses Gear: {gear_name}",
        )


def _normalize_list_field(value):
    """
    Normalisasi field list:
    - kalau None/empty -> []
    - kalau list -> strip semua item
    - kalau string "Nike, Adidas" -> ["Nike", "Adidas"]
    """
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return []


def _gear_to_json(gear: Gear):
    """Konversi object Gear ke dict JSON-friendly."""
    return {
        "id": str(gear.id),
        "sport_id": str(gear.sport.id) if gear.sport else None,
        "sport_name": gear.sport.name if gear.sport else "Unknown",
        "name": gear.name,
        "function": gear.function or "",
        "description": gear.description or "",
        "level": gear.level,
        "level_display": (
            gear.get_level_display()
            if hasattr(gear, "get_level_display")
            else gear.level
        ),
        "price_range": gear.price_range or "",
        "recommended_brands": gear.recommended_brands or [],
        "materials": gear.materials or [],
        "care_tips": gear.care_tips or "",
        "ecommerce_link": gear.ecommerce_link or "",
        "tags": gear.tags or [],
        "image": gear.image or "",
        "owner": gear.owner.username if gear.owner else None,
    }


# =========================
# HTML / WEB VIEWS
# =========================

def show_all_gears(request):
    """Halaman utama Gear Guide (HTML)."""
    gears = Gear.objects.select_related("sport").all()
    all_sports = Sport.objects.all().order_by("name")

    # filter sport
    selected_sport = request.GET.get("sport", "").strip().lower()
    if selected_sport:
        gears = [
            g for g in gears
            if g.sport and g.sport.name.lower() == selected_sport
        ]

    # filter level
    selected_level = request.GET.get("level", "").strip().lower()
    if selected_level:
        gears = [g for g in gears if g.level.lower() == selected_level]

    # filter: your gears
    view_filter = request.GET.get("view", "all")
    if view_filter == "your" and request.user.is_authenticated:
        gears = [
            g for g in gears
            if g.owner and g.owner.username == request.user.username
        ]

    context = {
        "gears": gears,
        "all_sports": all_sports,
        "view_filter": view_filter,
        "title": "Gear Guide",
    }
    return render(request, "gearguide/gearguide.html", context)


def show_gear_detail(request, gear_id):
    """Tampilkan detail 1 gear (HTML)."""
    try:
        gear = get_object_or_404(Gear, id=gear_id)
        _log_activity(request, gear.name)

        bump_view(
            key=f"gear:{gear.id}",
            title=gear.name,
            url=reverse("gearguide:card_details", kwargs={"gear_id": gear.id}),
            category="Gear",
            image=(
                gear.image.url
                if getattr(gear, "image", None)
                and hasattr(gear.image, "url")
                else (gear.image or "")
            ),
            request=request,
            dedupe_seconds=60,
        )

        return render(
            request,
            "gearguide/card_details.html",
            {"gear": gear, "is_from_db": True},
        )
    except Exception:
        raise Http404("Gear tidak ditemukan.")


@login_required(login_url="/accounts/login/")
def add_gear(request):
    """
    Tambah gear baru via form HTML (web).
    HANYA boleh admin (staff/superuser).
    """
    if not admin_only(request.user):
        # User biasa yang nekat akses URL langsung
        return HttpResponseForbidden("❌ Hanya admin yang boleh menambahkan gear.")

    sports = Sport.objects.all()

    if request.method == "POST":
        try:
            name = request.POST.get("name")
            description = request.POST.get("description")

            sport_input = request.POST.get("sport")
            sport = None
            if sport_input:
                sport = (
                    Sport.objects.filter(id=sport_input).first()
                    or Sport.objects.filter(name__iexact=sport_input).first()
                )

            new_gear = Gear.objects.create(
                sport=sport,
                name=name,
                description=description,
                function=request.POST.get("function"),
                image=request.POST.get("image"),
                price_range=request.POST.get("price_range"),
                ecommerce_link=request.POST.get("ecommerce_link"),
                level=request.POST.get("level") or "beginner",
                recommended_brands=_normalize_list_field(
                    request.POST.get("recommended_brands", "")
                ),
                materials=_normalize_list_field(
                    request.POST.get("materials", "")
                ),
                care_tips=request.POST.get("care_tips"),
                tags=_normalize_list_field(request.POST.get("tags", "")),
                owner=request.user,
            )

            ActivityLog.objects.create(
                user=request.user,
                action_type="CREATE",
                description=(
                    f"User '{request.user.username}' "
                    f"menambahkan gear '{new_gear.name}'"
                ),
            )
            messages.success(
                request, f"✅ Gear '{new_gear.name}' berhasil ditambahkan!"
            )
            return redirect("gearguide:show_all_gears")

        except Exception as e:
            traceback.print_exc()
            messages.error(request, f"❌ Gagal menambahkan gear: {e}")

    return render(
        request,
        "gear_app/gear_form.html",
        {"sports": sports, "edit_mode": False},
    )


@login_required(login_url="/accounts/login/")
def edit_gear(request, gear_id):
    """Edit gear (hanya admin atau pemilik) via web (AJAX)."""
    gear = get_object_or_404(Gear, id=gear_id)

    if not (admin_only(request.user) or gear.owner == request.user):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(
                {
                    "ok": False,
                    "message": "❌ Hanya admin atau pemilik gear yang dapat mengedit gear ini.",
                },
                status=403,
            )
        return HttpResponseForbidden(
            "❌ Kamu tidak punya izin untuk mengedit gear ini."
        )

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
            gear.recommended_brands = _normalize_list_field(
                request.POST.get("recommended_brands", "")
            )
            gear.materials = _normalize_list_field(
                request.POST.get("materials", "")
            )
            gear.care_tips = request.POST.get("care_tips")
            gear.tags = _normalize_list_field(request.POST.get("tags", ""))
            gear.save()

            ActivityLog.objects.create(
                user=request.user,
                action_type="UPDATE",
                description=(
                    f"User '{request.user.username}' "
                    f"mengedit gear '{gear.name}'"
                ),
            )
            return JsonResponse(
                {"ok": True, "message": "✅ Gear berhasil diperbarui!"}
            )

        except Exception as e:
            traceback.print_exc()
            return JsonResponse(
                {"ok": False, "message": f"❌ Gagal memperbarui gear: {e}"},
                status=400,
            )

    return JsonResponse(
        {"ok": False, "message": "❌ Metode tidak valid."}, status=405
    )


@login_required(login_url="/accounts/login/")
@csrf_exempt
def delete_gear(request, gear_id):
    """Hapus gear (hanya admin/superuser) via web (AJAX)."""
    gear = get_object_or_404(Gear, id=gear_id)

    if not admin_only(request.user):
        return JsonResponse(
            {"ok": False, "message": "❌ Hanya admin yang dapat menghapus gear."},
            status=403,
        )

    if request.method == "POST":
        gear_name = gear.name
        gear.delete()

        ActivityLog.objects.create(
            user=request.user,
            action_type="DELETE",
            description=(
                f"Admin '{request.user.username}' "
                f"menghapus gear '{gear_name}'"
            ),
        )

        return JsonResponse(
            {"ok": True, "message": f"🗑️ Gear '{gear_name}' berhasil dihapus!"}
        )

    return JsonResponse(
        {"ok": False, "message": "❌ Metode tidak valid."}, status=405
    )


@require_http_methods(["GET"])
def get_gear_json(request, gear_id):
    """Endpoint JSON ambil 1 gear (web/AJAX)."""
    try:
        gear = Gear.objects.filter(id=gear_id).first()
        if not gear:
            return JsonResponse(
                {"ok": False, "error": "Gear tidak ditemukan."}, status=404
            )

        data = _gear_to_json(gear)
        data.update(
            {
                "recommended_brands_text": ", ".join(data["recommended_brands"]),
                "materials_text": ", ".join(data["materials"]),
                "tags_text": ", ".join(data["tags"]),
            }
        )
        return JsonResponse({"ok": True, "data": data}, status=200)

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


def get_all_gears_json(request):
    """JSON list semua gear (web)."""
    gears = Gear.objects.select_related("sport").all()
    data = [_gear_to_json(g) for g in gears]

    response = {
        "ok": True,
        "count": len(data),
        "data": data,
    }
    return JsonResponse(response)

# =========================
# FLUTTER JSON API
# =========================

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import traceback

@csrf_exempt
def list_gears_flutter(request):
    """
    GET /gearguide/flutter/gears/
    Public, balikin JSON list gear untuk Flutter.
    """
    if request.method != "GET":
        return JsonResponse(
            {"ok": False, "error": "Method not allowed. Gunakan GET."},
            status=405,
        )

    gears = Gear.objects.select_related("sport").all()
    data = [_gear_to_json(g) for g in gears]

    return JsonResponse(
        {"ok": True, "count": len(data), "data": data},
        status=200,
    )

@csrf_exempt
def add_gear_flutter(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed. Gunakan POST."}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "Unauthenticated. Silakan login dulu."}, status=401)

    # =================================================================
    # 🔒 PENGECEKAN ADMIN (HANYA ADMIN BOLEH ADD)
    # =================================================================
    if not admin_only(request.user):
        return JsonResponse(
            {"ok": False, "error": "Forbidden. Hanya admin yang boleh menambah gear."},
            status=403,
        )
    # =================================================================

    try:
        # ... (Logika parsing data JSON/POST sama seperti sebelumnya) ...
        try:
            raw_body = request.body.decode("utf-8") or "{}"
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            data = request.POST.dict()

        name = data.get("name", "").strip()
        sport_id = data.get("sport")

        if not name or not sport_id:
            return JsonResponse({"ok": False, "error": "Field 'name' dan 'sport' wajib diisi."}, status=400)

        sport = Sport.objects.get(id=sport_id)

        gear = Gear.objects.create(
            name=name,
            sport=sport,
            function=data.get("function", ""),
            description=data.get("description", ""),
            image=data.get("image", ""),
            price_range=data.get("price_range", ""),
            ecommerce_link=data.get("ecommerce_link", ""),
            level=data.get("level", "beginner"),
            recommended_brands=_normalize_list_field(data.get("recommended_brands", [])),
            materials=_normalize_list_field(data.get("materials", [])),
            care_tips=data.get("care_tips", ""),
            tags=_normalize_list_field(data.get("tags", [])),
            owner=request.user,
        )

        return JsonResponse(
            {"ok": True, "message": "Gear berhasil dibuat", "data": _gear_to_json(gear)},
            status=201,
        )
    # ... (Exception handling sama) ...
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
    
@csrf_exempt
def edit_gear_flutter(request, gear_id):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed. Gunakan POST."}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "Unauthenticated. Silakan login dulu."}, status=401)

    gear = get_object_or_404(Gear, id=gear_id)

    # =================================================================
    # 🔒 PENGECEKAN ADMIN (STRICT)
    # Hapus "or gear.owner == request.user" agar pemilik biasa tidak bisa edit
    # =================================================================
    if not admin_only(request.user):
        return JsonResponse(
            {"ok": False, "error": "Forbidden. Hanya admin yang boleh mengedit gear."},
            status=403,
        )
    # =================================================================

    try:
        # ... (Sisa logika update sama persis seperti kodemu sebelumnya) ...
        try:
            raw_body = request.body.decode("utf-8") or "{}"
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            data = request.POST.dict()

        # Update fields
        sport_id = data.get("sport")
        if sport_id:
             try:
                gear.sport = Sport.objects.get(id=sport_id)
             except Sport.DoesNotExist:
                pass # Atau handle error
        
        gear.name = data.get("name", gear.name)
        gear.description = data.get("description", gear.description)
        # ... (update field lainnya) ...
        gear.save()

        return JsonResponse(
            {"ok": True, "message": f"Gear '{gear.name}' berhasil diperbarui.", "data": _gear_to_json(gear)},
            status=200,
        )
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)

@csrf_exempt
def delete_gear_flutter(request, gear_id):
    if request.method not in ["POST", "DELETE"]:
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "Unauthenticated."}, status=401)

    gear = get_object_or_404(Gear, id=gear_id)

    # =================================================================
    # 🔒 PENGECEKAN ADMIN (STRICT)
    # =================================================================
    if not admin_only(request.user):
        return JsonResponse(
            {"ok": False, "error": "Forbidden. Hanya admin yang boleh menghapus gear."},
            status=403,
        )
    # =================================================================

    gear_name = gear.name
    gear.delete()

    ActivityLog.objects.create(
        user=request.user,
        action_type="DELETE",
        description=f"Admin '{request.user.username}' menghapus gear '{gear_name}' (Flutter)",
    )

    return JsonResponse({"ok": True, "message": f"Gear '{gear_name}' berhasil dihapus."}, status=200)

@require_http_methods(["GET"])
def get_all_sports_json(request):
    """
    GET /gearguide/flutter/sports/
    Public, balikin JSON list semua sport (id & name) untuk Flutter.
    """
    try:
        # Ambil semua objek Sport
        sports = Sport.objects.all().order_by("name")

        # Konversi ke format yang dibutuhkan Flutter: List of {id: "1", name: "Sport Name"}
        data = [
            {
                "id": str(s.id),  # Penting: ubah ID menjadi string
                "name": s.name,
            }
            for s in sports
        ]

        return JsonResponse(
            {"ok": True, "count": len(data), "data": data},
            status=200,
            safe=False  # Gunakan safe=False jika Anda hanya mengirim List (bukan dict utama)
        )

    except Exception as e:
        traceback.print_exc()
        return JsonResponse(
            {"ok": False, "error": f"Server error while fetching sports: {e}"},
            status=500,
        )
