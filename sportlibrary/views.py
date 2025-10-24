from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from pathlib import Path
import json
from profile_app.models import ActivityLog
from django.http import JsonResponse
from .models import Sport, SavedSport

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def _load_sports_json():
    """Baca data olahraga dari database/sports.json"""
    data_path = settings.BASE_DIR / 'database' / 'sports.json'
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _normalize_id(raw_id: str):
    """
    Terima:
      - "10"  -> 10
      - "00000000-0000-0000-0000-00000000000a" -> 10 (ambil segmen hex terakhir)
      - "00000000-0000-0000-0000-000000000003" -> 3
    Kalau gagal parse, balikin None.
    """
    s = str(raw_id).strip().lower()

    if s.isdigit():
        try:
            return int(s)
        except Exception:
            return None

    # UUID-like: ambil segmen terakhir setelah '-'
    if '-' in s:
        tail = s.split('-')[-1]
        try:
            return int(tail, 16)
        except Exception:
            return None

    # terakhir: coba hex langsung
    try:
        return int(s, 16)
    except Exception:
        return None


# -------------------------------------------------
# Views
# -------------------------------------------------
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
        # Get or create the sport in database
        sport = Sport.objects.get(id=sport_id)
        
        # Check if already saved
        saved_sport = SavedSport.objects.filter(user=request.user, sport=sport).first()
        
        if saved_sport:
            # Already saved, so remove it (toggle)
            saved_sport.delete()
            return JsonResponse({'status': 'removed', 'message': 'Sport removed from saved list'})
        else:
            # Not saved yet, so save it
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
    
    return redirect('sportlibrary:saved_sports')
