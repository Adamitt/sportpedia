from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
<<<<<<< Updated upstream
from gearguide.models import Gear
from sportlibrary.models import Sport
from profile_app.models import ActivityLog
from django.db import models

# only admin/staff
def admin_only(user):
    return user.is_staff or user.is_superuser

@user_passes_test(admin_only, login_url='/accounts/login/')
def dashboard(request):
    total_gears = Gear.objects.count()
    total_sports = Sport.objects.count()
    return render(request, 'dashboard/dashboard.html', {
        'total_gears': total_gears,
        'total_sports': total_sports,
    })


@user_passes_test(admin_only, login_url='/accounts/login/')
def manage_gear(request):
    gears = Gear.objects.select_related('sport').all()
    return render(request, 'gear_app/manage_gear.html', {'gears': gears})


@user_passes_test(admin_only, login_url='/accounts/login/')
def add_gear(request):
    sports = Sport.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        sport_id = request.POST.get('sport')
        sport = Sport.objects.get(id=sport_id) if sport_id else None
        function = request.POST.get('function')
        required = request.POST.get('required') == 'on'
        image = request.POST.get('image')
        price_range = request.POST.get('price_range')
        ecommerce_link = request.POST.get('ecommerce_link')
        level = request.POST.get('level') or 'beginner'
        recommended_brands = request.POST.getlist('recommended_brands')
        materials = request.POST.getlist('materials')
        care_tips = request.POST.get('care_tips')
        tags = request.POST.getlist('tags')

        Gear.objects.create(
            sport=sport,
            name=name,
            description=description,
            function=function,
            required=required,
            image=image,
            price_range=price_range,
            ecommerce_link=ecommerce_link,
            level=level,
            recommended_brands=recommended_brands,
            materials=materials,
            care_tips=care_tips,
            tags=tags,
        )

        try:
            ActivityLog.objects.create(
                user=request.user,
                action_type='ADMIN_CREATE',
                description=f"Admin menambahkan Gear: {new_gear.name}"
            )
            messages.success(request, '✅ Gear berhasil ditambahkan!')
            return redirect('admin_sportpedia:manage_gear')
        except Exception as e:
             messages.error(request, f'❌ Gagal menambahkan gear: {e}')

        messages.success(request, '✅ Gear berhasil ditambahkan!')
        return redirect('manage_gear')

    return render(request, 'gear_app/gear_form.html', {'sports': sports, 'edit_mode': False})


@user_passes_test(admin_only, login_url='/accounts/login/')
def edit_gear(request, gear_id):
    gear = get_object_or_404(Gear, id=gear_id)
    sports = Sport.objects.all()

    if request.method == 'POST':
        gear.name = request.POST.get('name')
        gear.description = request.POST.get('description')
        gear.function = request.POST.get('function')
        sport_id = request.POST.get('sport')
        if sport_id:
            gear.sport = Sport.objects.get(id=sport_id)
        gear.required = request.POST.get('required') == 'on'
        gear.image = request.POST.get('image')
        gear.price_range = request.POST.get('price_range')
        gear.ecommerce_link = request.POST.get('ecommerce_link')
        gear.level = request.POST.get('level')
        gear.recommended_brands = request.POST.getlist('recommended_brands')
        gear.materials = request.POST.getlist('materials')
        gear.care_tips = request.POST.get('care_tips')
        gear.tags = request.POST.getlist('tags')
        gear.save()

        messages.success(request, '✏️ Gear berhasil diperbarui!')
        return redirect('manage_gear')

    return render(request, 'gear_app/gear_form.html', {
        'gear': gear,
        'sports': sports,
        'edit_mode': True
    })


@user_passes_test(admin_only, login_url='/accounts/login/')
def delete_gear(request, gear_id):
    gear = get_object_or_404(Gear, id=gear_id)
    if request.method == 'POST':
        gear.delete()
        messages.success(request, '🗑️ Gear berhasil dihapus!')
        return redirect('manage_gear')

    # optional: show a confirmation page; here we redirect back if not POST
    return redirect('manage_gear')

@user_passes_test(admin_only, login_url='/accounts/login/')
def manage_library(request):
    """Lists all sports for admin management."""
    sports = Sport.objects.all().order_by('name') # Order alphabetically
    return render(request, 'library/manage_library.html', {'sports': sports})
    return render(request, 'gear_app/manage_gear.html', {'gears': gears})

@user_passes_test(admin_only, login_url='/accounts/login/')
def add_sport(request):
    """Handles adding a new sport."""
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category')
        difficulty = request.POST.get('difficulty')
        description = request.POST.get('description')
        history = request.POST.get('history')

        # ✅ versi parse_json_list yang aman dan fleksibel
        import json
        def parse_json_list(text):
            if not text:
                return []
            try:
                # Kalau user kirim string JSON (misal: '["rule1","rule2"]')
                data = json.loads(text)
                if isinstance(data, list):
                    return [str(item).strip() for item in data if str(item).strip()]
            except json.JSONDecodeError:
                # Kalau bukan JSON valid, pisahkan pakai koma
                return [item.strip() for item in text.split(',') if item.strip()]
            return []

        try:
            # 🔥 FIX: Get max ID from database and set next ID manually
            sports_objects = Sport.objects.all()
            id_sports=[int(sport.id) for sport in sports_objects]
            id_sports.sort()
            max_id = id_sports[-1] if id_sports else 0
            next_id = int(max_id or 0) + 1
            
            print(f"🔍 Debug: Max ID = {max_id}, Next ID = {next_id}")  # Debug
            
            # Create sport with manual ID
            new_sport = Sport(
                id=next_id,
                name=name,
                category=category,
                difficulty=difficulty,
                description=description,
                history=history,
                rules=parse_json_list(request.POST.get('rules', '')),
                techniques=parse_json_list(request.POST.get('techniques', '')),
                benefits=parse_json_list(request.POST.get('benefits', '')),
                popular_countries=parse_json_list(request.POST.get('popular_countries', '')),
                tags=parse_json_list(request.POST.get('tags', '')),
            )

            new_sport.save()
            
            messages.success(request, f'✅ Olahraga "{name}" berhasil ditambahkan!')
            return redirect('admin_sportpedia:manage_library')
            
        except Exception as e:
            import traceback
            print("❌ Error:")
            print(traceback.format_exc())
            messages.error(request, f'❌ Gagal menambahkan olahraga: {e}')

    return render(request, 'library/sport_form.html', {'edit_mode': False})

def edit_sport(request, sport_id):
    """Handles editing an existing sport."""
    sport = get_object_or_404(Sport, id=sport_id)

    if request.method == 'POST':
        sport.name = request.POST.get('name')
        sport.category = request.POST.get('category')
        sport.difficulty = request.POST.get('difficulty')
        sport.description = request.POST.get('description')
        sport.history = request.POST.get('history')

        rules_str = request.POST.get('rules', '')
        techniques_str = request.POST.get('techniques', '')
        benefits_str = request.POST.get('benefits', '')
        countries_str = request.POST.get('popular_countries', '')
        tags_str = request.POST.get('tags', '')

        def parse_json_list(text):
             if not text: return []
             return [item.strip() for item in text.split(',') if item.strip()]

        sport.rules = parse_json_list(rules_str)
        sport.techniques = parse_json_list(techniques_str)
        sport.benefits = parse_json_list(benefits_str)
        sport.popular_countries = parse_json_list(countries_str)
        sport.tags = parse_json_list(tags_str)

        try:
            sport.save()
            messages.success(request, f'✏️ Olahraga "{sport.name}" berhasil diperbarui!')
            return redirect('admin_sportpedia:manage_library')
        except Exception as e:
             messages.error(request, f'❌ Gagal memperbarui olahraga: {e}')
             return render(request, 'library/sport_form.html', {'sport': sport, 'edit_mode': True})

    context = {
        'sport': sport,
        'edit_mode': True,
        'rules_str': ', '.join(sport.rules),
        'techniques_str': ', '.join(sport.techniques),
        'benefits_str': ', '.join(sport.benefits),
        'countries_str': ', '.join(sport.popular_countries),
        'tags_str': ', '.join(sport.tags),
    }
    return render(request, 'library/sport_form.html', context)

@user_passes_test(admin_only, login_url='/accounts/login/')
def delete_sport(request, sport_id):
    """Handles deleting a sport."""
    sport = get_object_or_404(Sport, id=sport_id)
    sport_name = sport.name
    if request.method == 'POST':
        try:
            sport.delete()
            messages.success(request, f'🗑️ Olahraga "{sport_name}" berhasil dihapus!')
        except Exception as e:
            messages.error(request, f'❌ Gagal menghapus olahraga: {e}')
        return redirect('admin_sportpedia:manage_library')

    return redirect('admin_sportpedia:manage_library')
=======
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.utils import timezone
from .models import UserProfile, ActivityLog
import json


# ===================== API Views untuk Flutter =====================

@csrf_exempt
def api_get_profile(request):
    """GET /api/user/profile/ - Ambil profil user"""
    if not request.user.is_authenticated:
        return JsonResponse({"status": False, "message": "User tidak terautentikasi."}, status=401)
    
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    return JsonResponse({
        "status": True,
        "data": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": user.date_joined.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "profile": {
                "olahraga_favorit": profile.olahraga_favorit or "",
                "preferensi": profile.preferensi or "",
                "foto_profil": profile.foto_profil or "",
            }
        }
    }, status=200)


@csrf_exempt
def api_update_profile(request):
    """POST /api/user/profile/update/ - Update profil user"""
    if not request.user.is_authenticated:
        return JsonResponse({"status": False, "message": "User tidak terautentikasi."}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({"status": False, "message": "Method tidak valid."}, status=405)
    
    try:
        data = json.loads(request.body)
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        user.save()
        
        if 'olahraga_favorit' in data:
            profile.olahraga_favorit = data['olahraga_favorit']
        if 'preferensi' in data:
            profile.preferensi = data['preferensi']
        if 'foto_profil' in data:
            profile.foto_profil = data['foto_profil']
        profile.save()
        
        ActivityLog.objects.create(user=user, action_type='MODULE_ACCESS', description='Updated profile from mobile app')
        
        return JsonResponse({"status": True, "message": "Profil berhasil diupdate."}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "Invalid JSON data."}, status=400)
    except Exception as e:
        return JsonResponse({"status": False, "message": str(e)}, status=500)


@csrf_exempt
def api_get_activity(request):
    """GET /api/user/activity/ - Ambil riwayat aktivitas"""
    if not request.user.is_authenticated:
        return JsonResponse({"status": False, "message": "User tidak terautentikasi."}, status=401)
    
    activities = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:50]
    activity_list = [{
        "id": a.id,
        "action_type": a.action_type,
        "action_display": a.get_action_type_display(),
        "description": a.description,
        "timestamp": a.timestamp.isoformat(),
    } for a in activities]
    
    return JsonResponse({"status": True, "data": activity_list}, status=200)


@csrf_exempt
def api_log_activity(request):
    """POST /api/user/activity/log/ - Catat aktivitas baru"""
    if not request.user.is_authenticated:
        return JsonResponse({"status": False, "message": "User tidak terautentikasi."}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({"status": False, "message": "Method tidak valid."}, status=405)
    
    try:
        data = json.loads(request.body)
        action_type = data.get('action_type', 'MODULE_ACCESS')
        description = data.get('description', '')
        
        valid_actions = [choice[0] for choice in ActivityLog.ACTION_CHOICES]
        if action_type not in valid_actions:
            action_type = 'MODULE_ACCESS'
        
        activity = ActivityLog.objects.create(user=request.user, action_type=action_type, description=description)
        
        return JsonResponse({
            "status": True,
            "message": "Aktivitas berhasil dicatat.",
            "data": {
                "id": activity.id,
                "action_type": activity.action_type,
                "description": activity.description,
                "timestamp": activity.timestamp.isoformat(),
            }
        }, status=200)
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "Invalid JSON data."}, status=400)
    except Exception as e:
        return JsonResponse({"status": False, "message": str(e)}, status=500)


@csrf_exempt
def api_change_password(request):
    """POST /api/user/change-password/ - Ubah password"""
    if not request.user.is_authenticated:
        return JsonResponse({"status": False, "message": "User tidak terautentikasi."}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({"status": False, "message": "Method tidak valid."}, status=405)
    
    try:
        data = json.loads(request.body)
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        user = request.user
        
        if not user.check_password(old_password):
            return JsonResponse({"status": False, "message": "Password lama salah."}, status=400)
        
        if new_password != confirm_password:
            return JsonResponse({"status": False, "message": "Password baru tidak cocok."}, status=400)
        
        if len(new_password) < 8:
            return JsonResponse({"status": False, "message": "Password minimal 8 karakter."}, status=400)
        
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        
        ActivityLog.objects.create(user=user, action_type='MODULE_ACCESS', description='Changed password from mobile app')
        
        return JsonResponse({"status": True, "message": "Password berhasil diubah."}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "Invalid JSON data."}, status=400)
    except Exception as e:
        return JsonResponse({"status": False, "message": str(e)}, status=500)


@csrf_exempt
def api_change_email(request):
    """POST /api/user/change-email/ - Ubah email"""
    if not request.user.is_authenticated:
        return JsonResponse({"status": False, "message": "User tidak terautentikasi."}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({"status": False, "message": "Method tidak valid."}, status=405)
    
    try:
        data = json.loads(request.body)
        new_email = data.get('email', '').strip()
        password = data.get('password', '')
        
        user = request.user
        
        if not user.check_password(password):
            return JsonResponse({"status": False, "message": "Password salah."}, status=400)
        
        if not new_email or '@' not in new_email:
            return JsonResponse({"status": False, "message": "Format email tidak valid."}, status=400)
        
        if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
            return JsonResponse({"status": False, "message": "Email sudah digunakan."}, status=400)
        
        user.email = new_email
        user.save()
        
        ActivityLog.objects.create(user=user, action_type='MODULE_ACCESS', description='Changed email from mobile app')
        
        return JsonResponse({"status": True, "message": "Email berhasil diubah."}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "Invalid JSON data."}, status=400)
    except Exception as e:
        return JsonResponse({"status": False, "message": str(e)}, status=500)


@csrf_exempt
def api_delete_account(request):
    """POST /api/user/delete-account/ - Hapus akun"""
    if not request.user.is_authenticated:
        return JsonResponse({"status": False, "message": "User tidak terautentikasi."}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({"status": False, "message": "Method tidak valid."}, status=405)
    
    try:
        data = json.loads(request.body)
        password = data.get('password', '')
        
        user = request.user
        
        if not user.check_password(password):
            return JsonResponse({"status": False, "message": "Password salah."}, status=400)
        
        username = user.username
        user.delete()
        
        return JsonResponse({"status": True, "message": f"Akun {username} berhasil dihapus."}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "Invalid JSON data."}, status=400)
    except Exception as e:
        return JsonResponse({"status": False, "message": str(e)}, status=500)


@csrf_exempt
def api_get_stats(request):
    """GET /api/user/stats/ - Statistik profil"""
    if not request.user.is_authenticated:
        return JsonResponse({"status": False, "message": "User tidak terautentikasi."}, status=401)
    
    user = request.user
    activity_counts = ActivityLog.objects.filter(user=user).values('action_type').annotate(count=Count('id'))
    
    activity_stats = {item['action_type']: item['count'] for item in activity_counts}
    total_activities = ActivityLog.objects.filter(user=user).count()
    
    recent_activities = ActivityLog.objects.filter(user=user).order_by('-timestamp')[:5]
    recent_list = [{
        "action_type": a.action_type,
        "action_display": a.get_action_type_display(),
        "description": a.description,
        "timestamp": a.timestamp.isoformat(),
    } for a in recent_activities]
    
    return JsonResponse({
        "status": True,
        "data": {
            "total_activities": total_activities,
            "activity_breakdown": activity_stats,
            "recent_activities": recent_list,
            "member_since": user.date_joined.isoformat(),
            "days_as_member": (timezone.now() - user.date_joined).days,
        }
    }, status=200)


@csrf_exempt
def api_clear_activity(request):
    """POST /api/user/activity/clear/ - Hapus semua riwayat aktivitas"""
    if not request.user.is_authenticated:
        return JsonResponse({"status": False, "message": "User tidak terautentikasi."}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({"status": False, "message": "Method tidak valid."}, status=405)
    
    try:
        logs_deleted, _ = ActivityLog.objects.filter(user=request.user).delete()
        return JsonResponse({"status": True, "message": f"Berhasil menghapus {logs_deleted} aktivitas."}, status=200)
    except Exception as e:
        return JsonResponse({"status": False, "message": str(e)}, status=500)


# ===================== Web Views (HTML) =====================

@login_required(login_url='/accounts/login/')
def profile_page(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    recent_activities = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:10]

    context = {
        'user': request.user,
        'profile': profile,
        'aktivitas': recent_activities,
    }
    return render(request, 'profile_app/profile.html', context)


@login_required(login_url='/accounts/login/')
def pengaturan_akun(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    user = request.user

    if request.method == 'POST':
        email = request.POST.get('email')
        new_password = request.POST.get('password')
        olahraga_favorit = request.POST.get('olahraga_favorit')
        preferensi = request.POST.get('preferensi')
        foto_url = request.POST.get('foto_profil')

        if email and email != user.email:
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                messages.error(request, '❌ Email sudah digunakan.')
                return redirect('profile_app:pengaturan_akun')
            user.email = email

        if new_password:
            user.set_password(new_password)
            update_session_auth_hash(request, user)

        user.save()

        profile.olahraga_favorit = olahraga_favorit
        profile.preferensi = preferensi
        if foto_url:
            profile.foto_profil = foto_url
        profile.save()

        return redirect('profile_app:profile_page')

    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'profile_app/pengaturan_akun.html', context)

def profile_view(request):
    context = {
        'profile': request.user.userprofile,
        'user': request.user,
    }
    return render(request, 'profile_page/profile.html', context)

@login_required
@require_POST
def clear_activity_history(request):
    """Menghapus semua ActivityLog untuk user yang sedang login."""
    try:
        logs_deleted, _ = ActivityLog.objects.filter(user=request.user).delete()
        
        if logs_deleted > 0:
            messages.success(request, f'🧹 Semua riwayat aktivitas ({logs_deleted} item) berhasil dihapus.')
        else:
            messages.info(request, 'Tidak ada riwayat aktivitas untuk dihapus.')
            
    except Exception as e:
       messages.error(request, f'❌ Gagal menghapus riwayat aktivitas: {e}')

    return redirect('profile_app:profile_page')
>>>>>>> Stashed changes
