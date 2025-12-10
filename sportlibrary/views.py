from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from profile_app.models import ActivityLog
from .models import Sport, SavedSport
from django.urls import reverse
from metrics.utils import bump_view

# -----------------------------------------------------------------------------
# Web views (Django templates) - EXISTING CODE KEPT AS IS
# -----------------------------------------------------------------------------
def show_sports(request):
    sports = Sport.objects.all()
    saved_count = 0
    saved_sport_ids = []
    if request.user.is_authenticated:
        saved_sports = SavedSport.objects.filter(user=request.user).values_list('sport_id', flat=True)
        saved_sport_ids = list(saved_sports)
        saved_count = len(saved_sport_ids)

    context = {
        "sports": sports,
        "saved_count": saved_count,
        "saved_sport_ids": saved_sport_ids
    }
    return render(request, 'sportlibrary/sportlibrary.html', context)

def sport_detail(request, sport_id):
    sport = get_object_or_404(Sport, id=sport_id)
    bump_view(
        key=f"sport:{sport.id}",
        title=sport.name,
        url=reverse('sportlibrary:sport_detail', kwargs={'sport_id': sport.id}),
        category="Library",
        image="",
        request=request,
        dedupe_seconds=60,
    )
    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedSport.objects.filter(user=request.user, sport=sport).exists()
        ActivityLog.objects.create(
            user=request.user,
            action_type='MODULE_ACCESS',
            description=f"Mengakses Sport Library: {sport.name}"
        )
    context = {
        "sport": sport,
        "is_saved": is_saved
    }
    return render(request, 'sportlibrary/detail.html', context)

def saved_sports(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    saved = SavedSport.objects.filter(user=request.user).select_related('sport')
    indoor_count = sum(1 for s in saved if s.sport.category == 'Indoor')
    outdoor_count = sum(1 for s in saved if s.sport.category == 'Outdoor')
    context = {
        'saved_sports': saved,
        'indoor_count': indoor_count,
        'outdoor_count': outdoor_count
    }
    return render(request, 'bookmarklist.html', context)

@require_http_methods(["POST"])
def save_sport(request, sport_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    try:
        sport = Sport.objects.get(id=sport_id)
        saved_sport = SavedSport.objects.filter(user=request.user, sport=sport).first()
        if saved_sport:
            saved_sport.delete()
            return JsonResponse({'status': 'removed', 'message': 'Sport removed from saved list'})
        else:
            SavedSport.objects.create(user=request.user, sport=sport)
            return JsonResponse({'status': 'saved', 'message': 'Sport saved successfully'})
    except Sport.DoesNotExist:
        return JsonResponse({'error': 'Sport not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def remove_sport(request, saved_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    try:
        saved_sport = get_object_or_404(SavedSport, id=saved_id, user=request.user)
        saved_sport.delete()
        return JsonResponse({'status': 'removed', 'message': 'Sport removed successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["POST"])
def clear_all_sports(request):
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    SavedSport.objects.filter(user=request.user).delete()
    messages.success(request, 'Semua olahraga berhasil dihapus dari simpanan')
    return redirect('sportlibrary:saved_sports')

# -----------------------------------------------------------------------------
# API endpoints for Flutter / mobile
# -----------------------------------------------------------------------------

def show_sports_json(request):
    """
    Returns list of sports with 'is_saved' status for the current user.
    """
    sports = Sport.objects.all()
    data = []

    # Get saved sports IDs for authenticated user
    saved_sport_ids = set()
    if request.user.is_authenticated:
        saved_sport_ids = set(SavedSport.objects.filter(user=request.user).values_list('sport_id', flat=True))

    for sport in sports:
        image_url = ""
        if getattr(sport, 'image', None):
            try:
                image_url = request.build_absolute_uri(sport.image.url)
            except Exception:
                image_url = ""

        data.append({
            "id": sport.id,
            "name": sport.name,
            "category": sport.category,
            "difficulty": sport.difficulty,
            "description": sport.description,
            "history": sport.history,
            "rules": sport.rules,
            "techniques": sport.techniques,
            "benefits": sport.benefits,
            "popular_countries": sport.popular_countries,
            "tags": sport.tags,
            "image": image_url,
            "is_saved": sport.id in saved_sport_ids, # True if user favorited this sport
        })
    return JsonResponse(data, safe=False)

def sport_detail_json(request, sport_id):
    try:
        sport = Sport.objects.get(pk=sport_id)
        image_url = ""
        if getattr(sport, 'image', None):
            try:
                image_url = request.build_absolute_uri(sport.image.url)
            except Exception:
                image_url = ""
        
        # Check is_saved status
        is_saved = False
        if request.user.is_authenticated:
            is_saved = SavedSport.objects.filter(user=request.user, sport=sport).exists()

        data = {
            "id": sport.id,
            "name": sport.name,
            "category": sport.category,
            "difficulty": sport.difficulty,
            "description": sport.description,
            "history": sport.history,
            "rules": sport.rules,
            "techniques": sport.techniques,
            "benefits": sport.benefits,
            "popular_countries": sport.popular_countries,
            "tags": sport.tags,
            "image": image_url,
            "is_saved": is_saved
        }
        return JsonResponse(data)
    except Sport.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Sport not found'}, status=404)

# --- TAMBAHKAN INI DI BAGIAN BAWAH ---

def saved_sports_json(request):
    """
    API to retrieve ONLY sports bookmarked by the user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

    saved_sports = SavedSport.objects.filter(user=request.user).select_related('sport')
    
    data = []
    for item in saved_sports:
        sport = item.sport
        image_url = ""
        if getattr(sport, 'image', None):
            try:
                image_url = request.build_absolute_uri(sport.image.url)
            except Exception:
                image_url = ""

        data.append({
            "id": sport.id,
            "name": sport.name,
            "category": sport.category,
            "difficulty": sport.difficulty,
            "description": sport.description,
            "history": sport.history,
            "rules": sport.rules,
            "techniques": sport.techniques,
            "benefits": sport.benefits,
            "popular_countries": sport.popular_countries,
            "tags": sport.tags,
            "image": image_url,
            "is_saved": True, # Always true for this list
        })
    return JsonResponse(data, safe=False)

@csrf_exempt
def toggle_saved_sport(request, sport_id):
    """
    API to toggle favorite status (Save/Unsave) for Flutter.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

    if request.method == 'POST':
        try:
            sport = Sport.objects.get(id=sport_id)
            saved_sport, created = SavedSport.objects.get_or_create(user=request.user, sport=sport)
            
            if not created:
                # If it already exists, delete it (Unsave)
                saved_sport.delete()
                return JsonResponse({'status': 'removed', 'message': 'Sport removed from favorites'})
            else:
                # If it was created (Save)
                return JsonResponse({'status': 'saved', 'message': 'Sport added to favorites'})
                
        except Sport.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Sport not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@csrf_exempt
def create_sport_flutter(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8') or '{}')
            required_fields = ['name', 'category', 'difficulty', 'description', 'history']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({"status": "error", "message": f"Field '{field}' is required"}, status=400)

            new_sport = Sport.objects.create(
                name=data.get("name", ""),
                category=data.get("category", ""),
                difficulty=data.get("difficulty", ""),
                description=data.get("description", ""),
                history=data.get("history", ""),
                rules=data.get("rules", []),
                techniques=data.get("techniques", []),
                benefits=data.get("benefits", []),
                popular_countries=data.get("popular_countries", []),
                tags=data.get("tags", []),
                # image=None, # Image handling skipped for simplicity
            )

            if request.user.is_authenticated:
                ActivityLog.objects.create(
                    user=request.user,
                    action_type='ADMIN_CREATE',
                    description=f"Menambahkan olahraga baru: {new_sport.name}"
                )

            return JsonResponse({"status": "success", "message": "Sport created successfully"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

@csrf_exempt
def edit_sport_flutter(request, sport_id):
    if request.method == 'POST':
        try:
            sport = get_object_or_404(Sport, pk=sport_id)
            data = json.loads(request.body.decode('utf-8') or '{}')

            sport.name = data.get("name", sport.name)
            sport.category = data.get("category", sport.category)
            sport.difficulty = data.get("difficulty", sport.difficulty)
            sport.description = data.get("description", sport.description)
            sport.history = data.get("history", sport.history)
            sport.rules = data.get("rules", sport.rules)
            sport.techniques = data.get("techniques", sport.techniques)
            sport.benefits = data.get("benefits", sport.benefits)
            sport.popular_countries = data.get("popular_countries", sport.popular_countries)
            sport.tags = data.get("tags", sport.tags)
            sport.save()

            if request.user.is_authenticated:
                ActivityLog.objects.create(
                    user=request.user,
                    action_type='ADMIN_UPDATE',
                    description=f"Memperbarui olahraga: {sport.name}"
                )
            return JsonResponse({"status": "success", "message": "Sport updated successfully"}, status=200)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

@csrf_exempt
def delete_sport_flutter(request, sport_id):
    if request.method == 'POST':
        try:
            sport = Sport.objects.get(pk=sport_id)
            sport_name = sport.name
            sport.delete()
            if request.user.is_authenticated:
                ActivityLog.objects.create(
                    user=request.user,
                    action_type='ADMIN_DELETE',
                    description=f"Menghapus olahraga: {sport_name}"
                )
            return JsonResponse({"status": "success", "message": "Sport deleted successfully"}, status=200)
        except Sport.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Sport not found"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)