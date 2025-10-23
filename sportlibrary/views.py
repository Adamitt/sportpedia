from django.shortcuts import render, redirect
import json
from pathlib import Path
from django.http import JsonResponse
from django.utils import timezone
from profile_app.models import SportProgress, Sport
from .models import SavedSport
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from metrics.utils import bump_view
from django.conf import settings


def show_sports(request):
    data_path = settings.BASE_DIR / 'database' / 'sports.json'


    with open(data_path, 'r', encoding='utf-8') as file:
        sports = json.load(file)

    context = {"sports": sports}
    return render(request, 'sportlibrary/sportlibrary.html', context)


def sport_detail(request, sport_id):
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / 'database' / 'sports.json'

    with open(data_path, 'r', encoding='utf-8') as file:
        sports = json.load(file)

    sport = next((s for s in sports if s['id'] == sport_id), None)

    if not sport:
        return render(request, "404.html", status=404)

    context = {"sport": sport}
    ##
    key   = f"sportjson:{sport_id}"
    url   = reverse('sportlibrary:sport_detail', kwargs={'sport_id': sport_id})
    title = sport.get('name') or f"Sport #{sport_id}"
    image = sport.get('image') or sport.get('thumbnail') or ""
    bump_view(key, title=title, url=url, category="Library", image=image, request=request)

    return render(request, 'sportlibrary/detail.html', context)

# def saved_sports(request):
#     base_dir = Path(__file__).resolve().parent.parent
#     data_path = base_dir / 'database' / 'sports.json'
    
#     with open(data_path, 'r', encoding='utf-8') as file:
#         all_sports = json.load(file)
    
#     context = {"all_sports_json": json.dumps(all_sports)}
#     return render(request, 'bookmarklist.html', context)

def saved_sports(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    saved = SavedSport.objects.filter(user=request.user).select_related('sport')

    context = {
        "saved_sports": saved
    }
    return render(request, 'bookmarklist.html', context)


def update_progress(request, sport_id):
    if request.method == "POST" and request.user.is_authenticated:
        data = json.loads(request.body.decode('utf-8'))
        completed = data.get("completed", False)
        time_spent = data.get("time_spent", 0)

        # --- Cari data olahraga dari JSON ---
        base_dir = Path(__file__).resolve().parent.parent
        data_path = base_dir / 'database' / 'sports.json'
        with open(data_path, 'r', encoding='utf-8') as file:
            sports = json.load(file)

        sport_data = next((s for s in sports if s['id'] == sport_id), None)
        if not sport_data:
            return JsonResponse({"status": "not_found"}, status=404)

        # --- Sinkronisasi ke database Sport ---
        sport, _ = Sport.objects.get_or_create(
            id=sport_id,
            defaults={"name": sport_data["name"], "description": sport_data.get("description", "")}
        )

        # --- Simpan progress berdasarkan user ---
        progress, created = SportProgress.objects.get_or_create(
            user=request.user,
            sport=sport,
            defaults={"completed": completed, "time_spent": time_spent}
        )

        if not created:
            progress.time_spent += time_spent
            if completed:
                progress.completed = True
            progress.last_accessed = timezone.now()
            progress.save()

        return JsonResponse({"status": "success"})
    
    return JsonResponse({"status": "unauthorized"}, status=401)

@login_required
def get_saved_sports(request):
    """Ambil daftar olahraga tersimpan untuk user saat ini"""
    saved = SportProgress.objects.filter(user=request.user, completed=False)
    data = [{"id": s.sport.id, "name": s.sport.name, "category": s.sport.category, "difficulty": s.sport.difficulty} for s in saved]
    return JsonResponse(data, safe=False)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def toggle_saved_sport(request, sport_id):
    """Tambah/hapus olahraga dari daftar tersimpan user"""
    sport = Sport.objects.get(id=sport_id)
    progress, created = SportProgress.objects.get_or_create(user=request.user, sport=sport)
    if not created:
        progress.delete()  # kalau sudah ada, artinya user mau un-save
        return JsonResponse({"status": "removed"})
    return JsonResponse({"status": "saved"})