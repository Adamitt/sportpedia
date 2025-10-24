# landingpage/views.py
from pathlib import Path
import json
from urllib.parse import urlparse

from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Q

from metrics.models import ViewCounter
from .models import Testimonial
from gearguide.models import Gear
from sportlibrary.models import Sport


# =======================================================
#               HALAMAN UTAMA & PENCARIAN
# =======================================================

def _normalize_terms(q: str):
    """Mengubah query pencarian menjadi satu set istilah yang relevan."""
    query = (q or "").strip().lower()
    if not query:
        return set()
    alias_groups = [
        {"tenis", "tennis"},
        {"bulu tangkis", "badminton", "bulutangkis", "shuttle", "shuttlecock"},
        {"sepak bola", "sepakbola", "bola", "soccer", "football"},
        {"basket", "basketball", "bola basket"},
        {"voli", "volley", "volleyball"},
        {"renang", "swimming", "swim"},
        {"lari", "running", "track"},
    ]
    for group in alias_groups:
        if query in group:
            return group
    return {query}

def search(request):
    """Menangani logika pencarian untuk Gear dan Sport dari database."""
    q = request.GET.get("q", "").strip()
    terms = _normalize_terms(q)

    if not terms:
        return render(request, "landingpage/search_page.html", {
            "query": q, "gear_results": [], "sport_results": []
        })

    # Buat query pencarian dinamis
    gear_q = Q()
    sport_q = Q()
    for t in terms:
        gear_q |= (Q(name__icontains=t) | Q(description__icontains=t) | Q(sport__name__icontains=t))
        sport_q |= (Q(name__icontains=t) | Q(description__icontains=t))

    # Eksekusi query ke database
    gear_results = Gear.objects.filter(gear_q).select_related('sport').distinct()
    sport_results = Sport.objects.filter(sport_q).distinct()

    return render(request, "landingpage/search_page.html", {
        "query": q,
        "gear_results": gear_results,
        "sport_results": sport_results,
    })

def home(request):
    """Menampilkan halaman utama dengan section 'What's Hot'."""
    hot_qs = (ViewCounter.objects
              .filter(category__in=["Library", "Gear Guide"])
              .order_by("-views")[:3])
    
    # Logika untuk 'hot_items' tetap sama
    sports_map = {}
    try:
        with open(settings.BASE_DIR / "database" / "sports.json", "r", encoding="utf-8") as f:
            for s in json.load(f):
                sports_map[str(s.get("id"))] = s
    except Exception:
        pass

    hot_items = []
    for it in hot_qs:
        item = {"title": it.title, "url": it.url, "image": it.image, "category": it.category, "views": it.views}
        if it.category == "Library":
            try:
                segs = [seg for seg in urlparse(it.url).path.split("/") if seg]
                sport_id = segs[-1] if segs else None
                s = sports_map.get(str(sport_id))
                desc = (s.get("description") or s.get("history") or "") if s else ""
                item["excerpt"] = (desc[:140] + "…") if len(desc) > 140 else desc
            except Exception:
                item["excerpt"] = ""
        hot_items.append(item)

    return render(request, "home.html", {"hot_items": hot_items})


# =======================================================
#               ENDPOINT API UNTUK TESTIMONI (CRUD)
# =======================================================

def _serialize(t, request):
    """Mengubah objek Testimonial menjadi format JSON, termasuk status kepemilikan."""
    is_owner = False
    if request.user.is_authenticated:
        if request.user.is_superuser or (t.user and t.user.id == request.user.id):
            is_owner = True
    return {
        "id": t.id, "title": t.title, "text": t.text,
        "user": (t.user.get_full_name() or t.user.username) if t.user else "Guest",
        "category": t.category, "image_url": t.image.url if t.image else "",
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M"), "is_owner": is_owner,
    }

@require_GET
def api_testimonials_list(request):
    """READ: Mengambil daftar testimoni, mendukung filter."""
    cat = request.GET.get("category", "all")
    limit = int(request.GET.get("limit", 30))
    qs = Testimonial.objects.filter(is_approved=True).order_by("-id")
    if cat != "all":
        qs = qs.filter(category=cat)
    items = [_serialize(t, request) for t in qs[:limit]]
    return JsonResponse({"items": items}, status=200)

@require_POST
def api_testimonials_create(request):
    """CREATE: Membuat testimoni baru."""
    text = (request.POST.get("text") or "").strip()
    raw_title = (request.POST.get("title") or "").strip()
    category = request.POST.get("category", "library")
    image = request.FILES.get("image")

    if not text or category not in dict(Testimonial.CATEGORY_CHOICES):
        return HttpResponseBadRequest("Invalid form data.")

    title = raw_title if raw_title else (text[:60] + ("…" if len(text) > 60 else "")) or "Testimonial"
    user = request.user if request.user.is_authenticated else None
    is_approved_status = bool(user and user.is_superuser)

    t = Testimonial.objects.create(user=user, title=title, text=text, category=category, image=image, is_approved=is_approved_status)
    return JsonResponse({"ok": True, "item": _serialize(t, request)}, status=200)

@require_POST
def api_testimonials_update(request, pk):
    """UPDATE: Mengedit testimoni yang sudah ada."""
    testimonial = get_object_or_404(Testimonial, pk=pk)
    if not (request.user.is_superuser or (testimonial.user and testimonial.user.id == request.user.id)):
        return HttpResponseForbidden("You are not allowed to edit this testimonial.")

    testimonial.title = request.POST.get("title", testimonial.title).strip()
    testimonial.text = request.POST.get("text", testimonial.text).strip()
    new_category = request.POST.get("category")
    if new_category in dict(Testimonial.CATEGORY_CHOICES):
        testimonial.category = new_category
    if "image" in request.FILES:
        testimonial.image = request.FILES["image"]
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