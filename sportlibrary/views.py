from django.shortcuts import render
import json
from pathlib import Path
from profile_app.models import ActivityLog
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
from profile_app.models import SportProgress
from .models import Sport
from django.conf import settings
from django.db.models import F

def show_sports(request):
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / 'database' / 'sports.json'

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

    if request.user.is_authenticated:
        ActivityLog.objects.create(
            user=request.user,
            action_type='MODULE_ACCESS',
            description=f"Mengakses Sport Library: {sport.get('name', 'Olahraga Tidak Dikenal')}"
        )

    context = {"sport": sport}
    return render(request, 'sportlibrary/detail.html', context)

def saved_sports(request):
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / 'database' / 'sports.json'
    
    with open(data_path, 'r', encoding='utf-8') as file:
        all_sports = json.load(file)
    
    context = {"all_sports_json": json.dumps(all_sports)}
    return render(request, 'bookmarklist.html', context)

# --- NEW/UPDATED VIEW: update_progress ---
@csrf_exempt # Use this if sending CSRF token via JS is complex, otherwise remove & send token
@login_required
@require_POST
def update_progress(request, sport_id):
    """API endpoint to update time spent on a sport module."""
    try:
        # Get time spent from request body
        data = json.loads(request.body.decode('utf-8'))
        time_spent_session = int(data.get("time_spent", 0))

        if time_spent_session <= 0:
            return JsonResponse({"status": "no_time"}, status=400)

        # --- Get or Create Sport Object ---
        try:
            sport = Sport.objects.get(id=sport_id)
        except Sport.DoesNotExist:
            # If sport isn't in DB (e.g., first access), create from JSON
            data_path = settings.BASE_DIR / 'database' / 'sports.json'
            with open(data_path, 'r', encoding='utf-8') as file:
                sports_json = json.load(file)
            sport_data = next((s for s in sports_json if s['id'] == sport_id), None)
            if not sport_data:
                return JsonResponse({"status": "sport_not_found"}, status=404)
            
            sport = Sport.objects.create(
                id=sport_id,
                name=sport_data.get("name", ""),
                category=sport_data.get("category", ""),
                difficulty=sport_data.get("difficulty", ""),
                description=sport_data.get("description", ""),
                # Add other fields if necessary
            )

        # --- Get or Create SportProgress ---
        progress, created = SportProgress.objects.get_or_create(
            user=request.user,
            sport=sport,
            defaults={'time_spent': 0, 'completed': False} # Initial defaults
        )

        # --- Update Time Spent ---
        if not progress.completed: # Only update if not already completed
            # Atomically add time spent in this session
            progress.time_spent = F('time_spent') + time_spent_session
            progress.last_accessed = timezone.now() # Update last accessed time
            progress.save()

            # Refresh from DB to get the actual total time_spent after F() expression
            progress.refresh_from_db() 

            # Check if completed after update
            if progress.time_spent >= SportProgress.TARGET_SECONDS:
                progress.completed = True
                progress.save(update_fields=['completed']) # Only save the completed field

            return JsonResponse({"status": "success", "total_time": progress.time_spent, "completed": progress.completed})
        else:
            # Already completed, no need to update time further
             return JsonResponse({"status": "already_completed"})

    except json.JSONDecodeError:
        return JsonResponse({"status": "invalid_json"}, status=400)
    except ValueError:
         return JsonResponse({"status": "invalid_time"}, status=400)
    except Exception as e:
        # Log the error e for debugging
        print(f"Error updating progress: {e}") 
        return JsonResponse({"status": "error"}, status=500)