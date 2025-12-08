# landingpage/views.py
from pathlib import Path
import json
from urllib.parse import urlparse

from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.clickjacking import xframe_options_exempt
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.views import View
from django.db.models import Q

from metrics.models import ViewCounter
from .models import Testimonial
from gearguide.models import Gear
from sportlibrary.models import Sport
import re
from django.urls import reverse #cika
from metrics.utils import bump_view
# =======================================================
#               HALAMAN UTAMA & PENCARIAN
# =======================================================

def _normalize_terms(query):
    # A simple normalizer. Adjust as needed.
    terms = re.split(r'[^\w-]+', query.lower()) # Split by non-word chars
    return [term for term in terms if len(term) > 1] # Ignore short terms


# --- THIS IS THE CORRECTED SEARCH VIEW ---
def search(request):
    """Menangani logika pencarian untuk Gear dan Sport dari database DAN JSON."""
    # landingpage/views.py (di fungsi search)
    q = (request.GET.get("q") or request.GET.get("query") or request.GET.get("search") or "").strip()

    terms = _normalize_terms(q)

    # --- 1. Load Data (Hybrid Logic from show_all_gears) ---
    
    # Load Sports JSON first (for mapping)
    sports_path = settings.BASE_DIR / "database" / "sports.json"
    json_sports = []
    if sports_path.exists():
        with open(sports_path, "r", encoding="utf-8") as f:
            json_sports = json.load(f)
    sport_map = {str(s["id"]): s["name"] for s in json_sports}

    # Load Gears JSON
    gears_path = settings.BASE_DIR / "database" / "gears.json"
    json_gears = []
    if gears_path.exists():
        with open(gears_path, "r", encoding="utf-8") as f:
            json_gears = json.load(f)

    # Combine all gears into one list of dictionaries
    combined_gears = []


    # # ===== Dari JSON =====
    # for g in json_gears:
    #     sport_id = str(g.get("sport_id", ""))
    #     combined_gears.append({
    #         "id": g.get("id"),
    #         "sport": {"name": sport_map.get(sport_id, g.get("sport", "Unknown"))}, # Embed as dict
    #         "name": g.get("name", ""),
    #         "description": g.get("description", ""),
    #         "function": g.get("function", ""),
    #         "level": g.get("level", ""),
    #         "price_range": g.get("price_range", ""),
    #         "image": g.get("image", ""),
    #         # Add any other fields you want to search
    #     })


    # ===== Dari DB =====
    for g in Gear.objects.select_related("sport").all():
        combined_gears.append({
            "id": str(g.id),
            "sport": {"name": g.sport.name if g.sport else "Unknown"},
            "name": g.name or "",
            "description": g.description or "",
            "function": g.function or "",
            "level": g.get_level_display() or "",
            "price_range": g.price_range or "",
            "image": g.image or "", # Handle ImageField
            # Add any other fields you want to search

        })

        
    # Load Sports from DB (for Sport search results)
    sport_results_db = Sport.objects.all()

    # --- 2. Perform Search (In-Memory Python Filtering) ---

    gear_results = []
    sport_results = []

    if terms:
        for gear in combined_gears:
            # Build a searchable text string for each gear
            search_text = " ".join([
                gear.get('name', ''),
                gear.get('description', ''),
                gear.get('function', ''),
                gear.get('sport', {}).get('name', '')
            ]).lower()
            
            # Check if any search term is in the text
            if any(term in search_text for term in terms):
                gear_results.append(gear)

        for sport in sport_results_db:
            # Build a searchable text string for each sport
            search_text = " ".join([
                sport.name,
                sport.description,
                sport.history
            ]).lower()
            
            if any(term in search_text for term in terms):
                sport_results.append(sport)

    # --- 3. Render Results ---
    return render(request, "landingpage/search_page.html", {
        "query": q,
        "gear_results": gear_results,   # This is now a list of dicts
        "sport_results": sport_results, # This is a QuerySet/list of Sport objects
    })

def _norm_cat(cat: str) -> str:
    c = (cat or "").strip().lower()
    if c in {"gear", "gear guide", "gearguide"}:
        return "Gear"
    if c in {"library"}:
        return "Library"
    return cat or ""

def _load_sports_map():
    sports_map = {}
    try:
        sports_path = settings.BASE_DIR / "database" / "sports.json"
        if sports_path.exists():
            with open(sports_path, "r", encoding="utf-8") as f:
                for s in json.load(f):
                    sports_map[str(s.get("id"))] = s
    except Exception:
        pass
    return sports_map

def _build_hot_items(limit=3):
    hot_qs = (
        ViewCounter.objects.filter(category__in=["Library", "Gear", "Gear Guide"])
        .order_by("-views", "-last_seen")[:limit]
    )
    sports_map = _load_sports_map()
    hot_items = []
    for it in hot_qs:
        cat = _norm_cat(it.category)
        item = {
            "title": it.title,
            "url": it.url,
            "image": it.image,
            "category": cat,
            "views": it.views,
        }
        if cat == "Library":
            try:
                segs = [seg for seg in urlparse(it.url).path.split("/") if seg]
                sport_id = segs[-1] if segs else None
                sport_data = sports_map.get(str(sport_id))
                desc = (sport_data.get("description") or sport_data.get("history") or "") if sport_data else ""
                item["excerpt"] = (desc[:140] + "…") if len(desc) > 140 else desc
            except Exception:
                item["excerpt"] = ""
        hot_items.append(item)
    return hot_items

def home(request):
    """Menampilkan halaman utama dengan section 'What's Hot'."""
    hot_items = _build_hot_items(limit=3)
    return render(request, "home.html", {"hot_items": hot_items})

# =======================================================
#               ENDPOINT API UNTUK TESTIMONI (CRUD)
# =======================================================
# ---- serializer
def _parse_payload(request):
    content_type = (request.content_type or "").split(";")[0].strip().lower()
    if content_type == "application/json":
        try:
            body = request.body.decode("utf-8")
        except AttributeError:
            body = request.body
        if not body:
            return {}
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON payload.")
        if isinstance(payload, dict):
            return payload
        return {}
    return request.POST

def _serialize(t, request):
    is_owner = False
    if request.user.is_authenticated:
        if request.user.is_superuser or (t.user and t.user_id == request.user.id):
            is_owner = True

    return {
        "id": t.id,
        "title": t.title,
        "text": t.text,
        "user": (t.user.get_full_name() or t.user.username) if t.user else "Guest",
        "category": t.category,
        "image_url": t.image_url or "",
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M"),
        "is_owner": is_owner,
    }
def _add_cors_headers(response):
    """Helper untuk menambahkan CORS headers."""
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRFToken"
    response["Access-Control-Allow-Credentials"] = "true"
    return response

@ensure_csrf_cookie
@require_GET
def api_csrf_token(request):
    """GET: Endpoint untuk mendapatkan CSRF token (untuk Flutter)."""
    token = get_token(request)
    response = JsonResponse({"csrfToken": token}, status=200)
    return _add_cors_headers(response)

@ensure_csrf_cookie
@require_GET
def api_testimonials_list(request):
    """READ: Mengambil daftar testimoni, mendukung filter."""
    if request.method == "OPTIONS":
        response = HttpResponseBadRequest()
        return _add_cors_headers(response)
    
    if request.method != "GET":
        response = HttpResponseBadRequest("Method not allowed")
        return _add_cors_headers(response)
    
    cat = request.GET.get("category", "all")
    limit = int(request.GET.get("limit", 30))
    qs = Testimonial.objects.all().order_by("-id")  # ⚡ ubah bagian ini
    if cat != "all":
        qs = qs.filter(category=cat)
    items = [_serialize(t, request) for t in qs[:limit]]
    response = JsonResponse({"items": items}, status=200)
    return _add_cors_headers(response)
@ensure_csrf_cookie
@require_POST
def api_testimonials_create(request):
    """CREATE: Membuat testimoni baru."""
    # CSRF protection tetap aktif, tapi support dari Flutter dengan header X-CSRFToken
    try:
        payload = _parse_payload(request)
    except ValueError:
        response = HttpResponseBadRequest("Invalid JSON payload.")
        return _add_cors_headers(response)

    text = (payload.get("text") or "").strip()
    raw_title = (payload.get("title") or "").strip()
    category = payload.get("category", "library")
    image_url = (payload.get("image_url") or "").strip()

    if not text or category not in dict(Testimonial.CATEGORY_CHOICES):
        return HttpResponseBadRequest("Invalid form data.")

    title = raw_title if raw_title else (text[:60] + ("…" if len(text) > 60 else "")) or "Testimonial"
    user = request.user if request.user.is_authenticated else None
    is_approved_status = bool(user and user.is_superuser)

    t = Testimonial.objects.create(
        user=user,
        title=title,
        text=text,
        category=category,
        image_url=image_url,
        is_approved=is_approved_status,
    )
    response = JsonResponse({"ok": True, "item": _serialize(t, request)}, status=200)
    return _add_cors_headers(response)

@require_POST
def api_testimonials_update(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    if not (request.user.is_superuser or (testimonial.user and testimonial.user_id == request.user.id)):
        return HttpResponseForbidden("You are not allowed to edit this testimonial.")

    try:
        payload = _parse_payload(request)
    except ValueError:
        return HttpResponseBadRequest("Invalid JSON payload.")

    testimonial.title = payload.get("title", testimonial.title).strip()
    testimonial.text = payload.get("text", testimonial.text).strip()
    new_category = payload.get("category")
    if new_category in dict(Testimonial.CATEGORY_CHOICES):
        testimonial.category = new_category

    if "image_url" in payload:
        testimonial.image_url = (payload.get("image_url") or "").strip()

    testimonial.save()
    return JsonResponse({"status": "success", "item": _serialize(testimonial, request)})

@require_POST
def api_testimonials_delete(request, pk):
    """DELETE: Menghapus testimoni."""
    testimonial = get_object_or_404(Testimonial, pk=pk)
    if not (request.user.is_superuser or (testimonial.user and testimonial.user.id == request.user.id)):
        return HttpResponseForbidden("You are not allowed to delete this testimonial.")
    testimonial.delete()
    return JsonResponse({"status": "success"})


@ensure_csrf_cookie
@require_GET
def api_popular_categories(request):
    """GET: List What's Hot items dari ViewCounter (read-only, sesuai logic Django asli)."""
    if request.method == "OPTIONS":
        response = JsonResponse({}, status=200)
        return _add_cors_headers(response)
    
    if request.method != "GET":
        response = HttpResponseBadRequest("Method not allowed")
        return _add_cors_headers(response)
    
    limit_param = request.GET.get("limit", 3)
    try:
        limit = int(limit_param)
    except (TypeError, ValueError):
        limit = 3
    limit = max(1, min(limit, 10))
    items = _build_hot_items(limit=limit)
    response = JsonResponse({"items": items}, status=200)
    return _add_cors_headers(response)

@ensure_csrf_cookie
@require_GET
def api_search(request):
    """GET: API Search untuk Gear dan Sport (sesuai logic Django search view)."""
    if request.method == "OPTIONS":
        response = JsonResponse({}, status=200)
        return _add_cors_headers(response)
    
    if request.method != "GET":
        response = HttpResponseBadRequest("Method not allowed")
        return _add_cors_headers(response)
    
    q = (request.GET.get("q") or request.GET.get("query") or request.GET.get("search") or "").strip()
    
    terms = _normalize_terms(q)
    
    # Load Sports JSON first (for mapping)
    sports_path = settings.BASE_DIR / "database" / "sports.json"
    json_sports = []
    if sports_path.exists():
        with open(sports_path, "r", encoding="utf-8") as f:
            json_sports = json.load(f)
    sport_map = {str(s["id"]): s["name"] for s in json_sports}
    
    # Load Gears from DB (sesuai logic Django asli - hanya dari DB, bukan JSON)
    combined_gears = []
    for g in Gear.objects.select_related("sport").all():
        combined_gears.append({
            "id": str(g.id),
            "sport": {"name": g.sport.name if g.sport else "Unknown"},
            "name": g.name or "",
            "description": g.description or "",
            "function": g.function or "",
            "level": g.get_level_display() or "",
            "price_range": g.price_range or "",
            "image": g.image or "",
        })
    
    # Load Sports from DB
    sport_results_db = Sport.objects.all()
    
    # Perform Search
    gear_results = []
    sport_results = []
    
    if terms:
        for gear in combined_gears:
            search_text = " ".join([
                gear.get('name', ''),
                gear.get('description', ''),
                gear.get('function', ''),
                gear.get('sport', {}).get('name', '')
            ]).lower()
            
            if any(term in search_text for term in terms):
                gear_results.append(gear)
        
        for sport in sport_results_db:
            search_text = " ".join([
                sport.name,
                sport.description or "",
                sport.history or ""
            ]).lower()
            
            if any(term in search_text for term in terms):
                sport_results.append({
                    "id": sport.id,
                    "name": sport.name,
                    "description": sport.description or "",
                    "history": sport.history or "",
                })
    
    response = JsonResponse({
        "query": q,
        "gear_results": gear_results,
        "sport_results": sport_results,
    }, status=200)
    return _add_cors_headers(response)
