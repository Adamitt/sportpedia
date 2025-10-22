from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now
from datetime import timedelta
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from .models import PageHit, Testimonial

# =======================================================
#               VIEWS UNTUK HALAMAN UTAMA
# =======================================================

def home(request):
    # Logika untuk 'hot pages' tidak kita gunakan di template, tapi biarkan saja
    seven_days_ago = now() - timedelta(days=7)
    hot_pages = (PageHit.objects
                 .filter(last_hit__gte=seven_days_ago)
                 .order_by('-hits','-last_hit')[:3])
    return render(request, "home.html", {"hot_pages": hot_pages})

def search(request):
    q = request.GET.get("q", "")
    return render(request, "search_results.html", {"q": q, "results": []})

# =======================================================
#               ENDPOINT API UNTUK TESTIMONI
# =======================================================

def _serialize(t, request):
    """
    Mengubah objek Testimonial menjadi format JSON (dictionary).
    Juga menambahkan flag 'is_owner' untuk frontend.
    """
    is_owner = False
    # Pengguna dianggap pemilik jika dia adalah superuser,
    # atau jika dia login DAN ID-nya cocok dengan pembuat testimoni.
    if request.user.is_authenticated:
        if request.user.is_superuser or (t.user and t.user.id == request.user.id):
            is_owner = True

    return {
        "id": t.id,
        "title": t.title,
        "text": t.text,
        "user": (t.user.get_full_name() or t.user.username) if t.user else "Guest",
        "category": t.category,
        "image_url": t.image.url if t.image else "",
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M"),
        "is_owner": is_owner,
    }

@require_GET
def api_testimonials_list(request):
    """Mengambil daftar testimoni, mendukung filter berdasarkan kategori."""
    cat = request.GET.get("category", "all")
    limit  = int(request.GET.get("limit", 30))
    qs = Testimonial.objects.filter(is_approved=True).order_by("-id")
    if cat != "all":
        qs = qs.filter(category=cat)
    
    items = [_serialize(t, request) for t in qs[:limit]]
    return JsonResponse({"items": items})

@require_POST
def api_testimonials_create(request):
    """Membuat testimoni baru."""
    title = (request.POST.get("title") or "").strip()
    text  = (request.POST.get("text") or "").strip()
    category = request.POST.get("category", "library")
    image = request.FILES.get("image")

    if not title or not text or category not in dict(Testimonial.CATEGORY_CHOICES):
        return HttpResponseBadRequest("Invalid form data.")

    user = request.user if request.user.is_authenticated else None
    
    # Testimoni dari superuser langsung disetujui.
    is_approved_status = bool(user and user.is_superuser)

    t = Testimonial.objects.create(
        user=user, title=title, text=text,
        category=category, image=image,
        is_approved=is_approved_status
    )
    return JsonResponse({"ok": True, "item": _serialize(t, request)})

@require_POST
def api_testimonials_update(request, pk):
    """Mengedit testimoni yang sudah ada."""
    testimonial = get_object_or_404(Testimonial, pk=pk)

    # Keamanan: Hanya pemilik atau superuser yang bisa mengedit.
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
    """Menghapus testimoni."""
    testimonial = get_object_or_404(Testimonial, pk=pk)
    
    # Keamanan: Hanya pemilik atau superuser yang bisa menghapus.
    if not (request.user.is_superuser or (testimonial.user and testimonial.user.id == request.user.id)):
        return HttpResponseForbidden("You are not allowed to delete this testimonial.")
        
    testimonial.delete()
    return JsonResponse({"status": "success"}) 