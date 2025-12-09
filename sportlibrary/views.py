from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt # Tambah csrf_exempt
from django.views.decorators.http import require_http_methods
from pathlib import Path
import json
from profile_app.models import ActivityLog
from .models import Sport, SavedSport

<<<<<<< Updated upstream
def show_sports(request):
    # Kalau database kosong, sync dari JSON
    if Sport.objects.count() == 0:
        from pathlib import Path
        import json

        base_dir = Path(__file__).resolve().parent.parent
        data_path = base_dir / 'database' / 'sports.json'
        
        with open(data_path, 'r', encoding='utf-8') as file:
            sports_json = json.load(file)
        
        for s in sports_json:
            Sport.objects.get_or_create(
                id=s['id'],
                defaults={
                    'name': s['name'],
                    'category': s['category'],
                    'difficulty': s['difficulty'],
                    'description': s['description'],
                    'history': s['history'],
                    'rules': s.get('rules', []),
                    'techniques': s.get('techniques', []),
                    'benefits': s.get('benefits', []),
                    'popular_countries': s.get('popular_countries', []),
                    'tags': s.get('tags', []),
                }
            )

    # Setelah itu ambil semua sport dari database
=======
# ==============================================================================
# BAGIAN 1: VIEWS UNTUK WEB (DJANGO TEMPLATE HTML) - KODE LAMA KAMU
# ==============================================================================

def show_sports(request):
    # Ambil semua sport dari database
>>>>>>> Stashed changes
    sports = Sport.objects.all()

    # Get saved sports for current user
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
<<<<<<< Updated upstream
=======
    
    # Naikkan counter untuk What's Hot
    bump_view(
        key=f"sport:{sport.id}",
        title=sport.name,
        url=reverse('sportlibrary:sport_detail', kwargs={'sport_id': sport.id}),
        category="Library",       
        image="",                
        request=request,
        dedupe_seconds=60,        
    )
>>>>>>> Stashed changes

    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedSport.objects.filter(
            user=request.user,
            sport=sport
        ).exists()
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
    
    # Calculate stats
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
        saved_sport = get_object_or_404(
            SavedSport, 
            id=saved_id, 
            user=request.user
        )
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
    
<<<<<<< Updated upstream
    return redirect('sportlibrary:saved_sports')
=======
    return redirect('sportlibrary:saved_sports')

# Tambahkan ini ke bagian bawah views.py yang sudah ada

# ==============================================================================
# BAGIAN 2: API KHUSUS FLUTTER (MOBILE) - KODE BARU
# ==============================================================================

# 1. API GET ALL SPORTS
def show_sports_json(request):
    sports = Sport.objects.all()
    data = []
    for sport in sports:
        # Logika untuk mendapatkan URL gambar
        image_url = ""
        if sport.image:
            image_url = request.build_absolute_uri(sport.image.url)
            
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
            "image": image_url, # Tambahkan ini!
        })
    return JsonResponse(data, safe=False)

def sport_detail_json(request, sport_id):
    try:
        sport = Sport.objects.get(pk=sport_id)
        
        image_url = ""
        if sport.image:
            image_url = request.build_absolute_uri(sport.image.url)

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
            "image": image_url, # Tambahkan ini!
        }
        return JsonResponse(data)
    except Sport.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Sport not found'}, status=404)
    
# 3. API CREATE
@csrf_exempt
def create_sport_flutter(request):
    """Create new sport from Flutter"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['name', 'category', 'difficulty', 'description', 'history']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        "status": "error",
                        "message": f"Field '{field}' is required"
                    }, status=400)
            
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
            )
            
            # Log activity if user is authenticated
            if request.user.is_authenticated:
                ActivityLog.objects.create(
                    user=request.user,
                    action_type='ADMIN_CREATE',
                    description=f"Menambahkan olahraga baru: {new_sport.name}"
                )
            
            return JsonResponse({
                "status": "success",
                "message": "Sport created successfully",
                "data": {
                    "id": new_sport.id,
                    "name": new_sport.name
                }
            }, status=200)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

# 4. API EDIT (UPDATE)
@csrf_exempt
def edit_sport_flutter(request, sport_id):
    """Update existing sport from Flutter"""
    if request.method == 'POST':
        try:
            sport = get_object_or_404(Sport, pk=sport_id)
            data = json.loads(request.body)

            # Update fields
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
            
            # Log activity if user is authenticated
            if request.user.is_authenticated:
                ActivityLog.objects.create(
                    user=request.user,
                    action_type='ADMIN_UPDATE',
                    description=f"Memperbarui olahraga: {sport.name}"
                )

            return JsonResponse({
                "status": "success",
                "message": "Sport updated successfully"
            }, status=200)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)

# 5. API DELETE
@csrf_exempt
def delete_sport_flutter(request, sport_id):
    """Delete sport from Flutter"""
    if request.method == 'POST':
        try:
            sport = Sport.objects.get(pk=sport_id)
            sport_name = sport.name
            
            sport.delete()
            
            # Log activity if user is authenticated
            if request.user.is_authenticated:
                ActivityLog.objects.create(
                    user=request.user,
                    action_type='ADMIN_DELETE',
                    description=f"Menghapus olahraga: {sport_name}"
                )
            
            return JsonResponse({
                "status": "success",
                "message": "Sport deleted successfully"
            }, status=200)
        except Sport.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": "Sport not found"
            }, status=404)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
    
    return JsonResponse({"status": "error", "message": "Method not allowed"}, status=405)
>>>>>>> Stashed changes
