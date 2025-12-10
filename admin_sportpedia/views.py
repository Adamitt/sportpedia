from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from gearguide.models import Gear
from sportlibrary.models import Sport
from profile_app.models import ActivityLog
from django.contrib.auth.models import User
from django.db.models import Q
from .forms import AdminUserCreationForm, AdminUserChangeForm
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import models
from django.views.decorators.csrf import csrf_exempt
import json
from pathlib import Path

# only admin/staff
def admin_only(user):
    return user.is_staff or user.is_superuser


# ===================== API Views untuk Flutter =====================

@csrf_exempt
def api_admin_dashboard(request):
    """API untuk mendapatkan data dashboard admin (untuk Flutter)"""
    # Cek apakah user sudah login dan adalah admin
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': False,
            'message': 'Anda harus login terlebih dahulu.'
        }, status=401)
    
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({
            'status': False,
            'message': 'Anda tidak memiliki akses ke halaman ini.'
        }, status=403)
    
    try:
        total_gears = Gear.objects.count()
        total_sports = Sport.objects.count()
        total_users = User.objects.count()
        total_admins = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).count()
        
        # Recent activity logs (last 10)
        recent_activities = ActivityLog.objects.all().order_by('-timestamp')[:10]
        activities_data = []
        for activity in recent_activities:
            activities_data.append({
                'id': activity.id,
                'user': activity.user.username if activity.user else 'Unknown',
                'action_type': activity.action_type,
                'description': activity.description,
                'timestamp': activity.timestamp.isoformat() if activity.timestamp else None,
            })
        
        return JsonResponse({
            'status': True,
            'message': 'Data dashboard berhasil diambil.',
            'data': {
                'total_sports': total_sports,
                'total_gears': total_gears,
                'total_users': total_users,
                'total_admins': total_admins,
                'recent_activities': activities_data,
                'user': {
                    'username': request.user.username,
                    'email': request.user.email,
                    'is_staff': request.user.is_staff,
                    'is_superuser': request.user.is_superuser,
                    'last_login': request.user.last_login.isoformat() if request.user.last_login else None,
                }
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'status': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)

@user_passes_test(admin_only, login_url='/accounts/login/')
def dashboard(request):
    """Halaman utama dashboard admin"""
    total_gears = Gear.objects.count()
    total_sports = Sport.objects.count()
    total_users_count = User.objects.count()

    return render(request, 'dashboard/dashboard.html', {
        'total_gears': total_gears,
        'total_users': total_users_count,
        'total_sports': total_sports,
    })



@user_passes_test(admin_only, login_url='/accounts/login/')
def manage_gear(request):
    db_gears = Gear.objects.select_related('sport').all().order_by('name')

    formatted_gears = []
    for g in db_gears:
        # Ambil owner
        owner_username = None
        if hasattr(g, 'user') and g.user:
            owner_username = g.user.username
        elif hasattr(g, 'owner') and g.owner:
            owner_username = g.owner.username
        elif hasattr(g, 'created_by') and g.created_by:
            owner_username = g.created_by.username

        formatted_gears.append({
            "id": str(g.id),
            "name": g.name,
            "sport": g.sport.name if g.sport else "Tidak diketahui",
            "level": getattr(g, "get_level_display", lambda: g.level)(),
            "price_range": g.price_range or "-",
            "is_from_db": True,
            "owner": owner_username,
        })

    return render(request, 'gear_app/manage_gear.html', {'gears': formatted_gears})


@user_passes_test(admin_only, login_url='/accounts/login/')
def add_gear(request):
    sports = Sport.objects.all()

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description')
            sport_id = request.POST.get('sport')
            sport = Sport.objects.get(id=sport_id) if sport_id else None
            function = request.POST.get('function')
            image = request.POST.get('image')
            price_range = request.POST.get('price_range')
            ecommerce_link = request.POST.get('ecommerce_link')
            level = request.POST.get('level') or 'beginner'
            recommended_brands = [b.strip() for b in request.POST.get('recommended_brands', '').split(',') if b.strip()]
            materials = [m.strip() for m in request.POST.get('materials', '').split(',') if m.strip()]
            care_tips = request.POST.get('care_tips')
            tags = [t.strip() for t in request.POST.get('tags', '').split(',') if t.strip()]

            new_gear = Gear.objects.create(
                sport=sport,
                name=name,
                description=description,
                function=function,
                image=image,
                price_range=price_range,
                ecommerce_link=ecommerce_link,
                level=level,
                recommended_brands=recommended_brands,
                materials=materials,
                care_tips=care_tips,
                tags=tags,
            )

            ActivityLog.objects.create(
                user=request.user,
                action_type='ADMIN_CREATE',
                description=f"Admin menambahkan Gear: {new_gear.name}"
            )

            messages.success(request, '✅ Gear berhasil ditambahkan!')
            return redirect('admin_sportpedia:manage_gear')

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messages.error(request, f'❌ Gagal menambahkan gear: {e}')

    return render(request, 'gear_app/gear_form.html', {'sports': sports, 'edit_mode': False})


@user_passes_test(admin_only, login_url='/accounts/login/')
def edit_gear(request, gear_id):
    gear = get_object_or_404(Gear, id=gear_id)
    sports = Sport.objects.all()

    if request.method == 'POST':
        try:
            gear.name = request.POST.get('name')
            gear.description = request.POST.get('description')
            gear.function = request.POST.get('function')
            sport_id = request.POST.get('sport')
            if sport_id:
                gear.sport = Sport.objects.get(id=sport_id)
            gear.image = request.POST.get('image')
            gear.price_range = request.POST.get('price_range')
            gear.ecommerce_link = request.POST.get('ecommerce_link')
            gear.level = request.POST.get('level')
            gear.recommended_brands = [b.strip() for b in request.POST.get('recommended_brands', '').split(',') if b.strip()]
            gear.materials = [m.strip() for m in request.POST.get('materials', '').split(',') if m.strip()]
            gear.care_tips = request.POST.get('care_tips')
            gear.tags = [t.strip() for t in request.POST.get('tags', '').split(',') if t.strip()]
            gear.save()

            messages.success(request, '✏️ Gear berhasil diperbarui!')
            return redirect('admin_sportpedia:manage_gear')

        except Exception as e:
            messages.error(request, f'❌ Gagal memperbarui gear: {e}')

    return render(request, 'gear_app/gear_form.html', {
        'gear': gear,
        'sports': sports,
        'edit_mode': True
    })



@user_passes_test(admin_only, login_url='/accounts/login/')
def delete_gear(request, gear_id):
    gear = get_object_or_404(Gear, id=gear_id)
    if request.method == 'POST':
        gear_name = gear.name
        gear.delete()
        messages.success(request, f'🗑️ Gear "{gear_name}" berhasil dihapus!')
    return redirect('admin_sportpedia:manage_gear')

@user_passes_test(admin_only, login_url='/accounts/login/')
def manage_library(request):
    """Lists all sports for admin management."""
    sports = Sport.objects.all().order_by('name') # Order alphabetically
    return render(request, 'library/manage_library.html', {'sports': sports})

@user_passes_test(admin_only, login_url='/accounts/login/')
def add_sport(request):
    """Handles adding a new sport."""
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category')
        difficulty = request.POST.get('difficulty')
        description = request.POST.get('description')
        history = request.POST.get('history')

        import json
        def parse_json_list(text):
            if not text:
                return []
            try:
                data = json.loads(text)
                if isinstance(data, list):
                    return [str(item).strip() for item in data if str(item).strip()]
            except json.JSONDecodeError:
                return [item.strip() for item in text.split(',') if item.strip()]
            return []

        try:
            sports_objects = Sport.objects.all()
            id_sports=[int(sport.id) for sport in sports_objects]
            id_sports.sort()
            max_id = id_sports[-1] if id_sports else 0
            next_id = int(max_id or 0) + 1
            
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

@user_passes_test(admin_only, login_url='/accounts/login/')
def manage_admin(request):
    """Menampilkan halaman tabel admin dan modal."""
    admins = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).exclude(pk=request.user.pk).order_by('username')
    
    # --- PENTING: Kirim 'add_form' untuk placeholder modal ---
    add_form = AdminUserCreationForm() 
    
    context = {
        'admins': admins,
        'add_form': add_form # <-- Form ini diperlukan oleh template modal
    }
    return render(request, 'admin_app/manage_admin.html', context)

@user_passes_test(admin_only, login_url='/accounts/login/')
@require_POST # Hanya izinkan POST
def add_admin(request):
    """Menangani submit AJAX untuk menambah admin."""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Permintaan tidak valid.'}, status=400)

    form = AdminUserCreationForm(request.POST)
    if form.is_valid():
        try:
            new_admin = form.save()
            ActivityLog.objects.create(
                user=request.user, action_type='ADMIN_CREATE',
                description=f"Admin menambahkan admin baru: {new_admin.username}"
            )
            return JsonResponse({'success': True, 'message': f'Admin "{new_admin.username}" berhasil ditambahkan!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Gagal menambahkan admin: {e}'}, status=500)
    else:
        # Kirim error validasi form sebagai JSON
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@user_passes_test(admin_only, login_url='/accounts/login/')
@require_POST # Hanya izinkan POST
def edit_admin(request, admin_id):
    """Menangani submit AJAX untuk mengedit admin."""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
         return JsonResponse({'success': False, 'message': 'Permintaan tidak valid.'}, status=400)

    target_admin = get_object_or_404(User, pk=admin_id)
    if target_admin == request.user:
         return JsonResponse({'success': False, 'message': 'Anda tidak dapat mengedit akun Anda sendiri.'}, status=403)

    form = AdminUserChangeForm(request.POST, instance=target_admin)
    if form.is_valid():
        try:
            edited_admin = form.save()
            ActivityLog.objects.create(
                user=request.user, action_type='ADMIN_UPDATE',
                description=f"Admin memperbarui admin: {edited_admin.username}"
            )
            return JsonResponse({'success': True, 'message': f'Admin "{edited_admin.username}" berhasil diperbarui!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Gagal memperbarui admin: {e}'}, status=500)
    else:
        # Kirim error validasi form sebagai JSON
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@user_passes_test(admin_only, login_url='/accounts/login/')
def get_admin_data(request, admin_id):
    """API (GET) untuk mengambil data admin untuk modal edit."""
    
    # Hanya izinkan request AJAX
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Permintaan tidak valid'}, status=400)

    try:
        # Ambil data user yang akan di-edit
        target_admin = User.objects.get(pk=admin_id)
        
        # Siapkan data untuk dikirim sebagai JSON
        data = {
            'id': target_admin.id,
            'username': target_admin.username,
            'email': target_admin.email,
            'is_staff': target_admin.is_staff,
            'is_superuser': target_admin.is_superuser,
        }
        return JsonResponse(data) # Kirim data sebagai JSON
        
    except User.DoesNotExist:
         return JsonResponse({'error': 'User tidak ditemukan'}, status=404)
    except Exception as e:
         # Log error jika perlu: print(f"Error in get_admin_data: {e}")
         return JsonResponse({'error': 'Internal server error'}, status=500)


# ===================== API Views untuk Flutter - Kelola Admin =====================

@csrf_exempt
def api_get_admins(request):
    """API untuk mendapatkan daftar admin (untuk Flutter)"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': False,
            'message': 'Anda harus login terlebih dahulu.'
        }, status=401)
    
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({
            'status': False,
            'message': 'Anda tidak memiliki akses ke halaman ini.'
        }, status=403)
    
    try:
        admins = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).order_by('username')
        admins_data = []
        for admin in admins:
            admins_data.append({
                'id': admin.id,
                'username': admin.username,
                'email': admin.email,
                'is_staff': admin.is_staff,
                'is_superuser': admin.is_superuser,
                'date_joined': admin.date_joined.isoformat() if admin.date_joined else None,
                'last_login': admin.last_login.isoformat() if admin.last_login else None,
                'is_current_user': admin.id == request.user.id,
            })
        
        return JsonResponse({
            'status': True,
            'message': 'Data admin berhasil diambil.',
            'data': admins_data
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'status': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


@csrf_exempt
def api_add_admin(request):
    """API untuk menambah admin baru (untuk Flutter)"""
    if request.method != 'POST':
        return JsonResponse({
            'status': False,
            'message': 'Method tidak diizinkan.'
        }, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': False,
            'message': 'Anda harus login terlebih dahulu.'
        }, status=401)
    
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({
            'status': False,
            'message': 'Anda tidak memiliki akses.'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email', '')
        password = data.get('password')
        is_staff = data.get('is_staff', True)
        is_superuser = data.get('is_superuser', False)
        
        if not username or not password:
            return JsonResponse({
                'status': False,
                'message': 'Username dan password harus diisi.'
            }, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'status': False,
                'message': 'Username sudah digunakan.'
            }, status=400)
        
        if email and User.objects.filter(email=email).exists():
            return JsonResponse({
                'status': False,
                'message': 'Email sudah digunakan.'
            }, status=400)
        
        new_admin = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        new_admin.is_staff = is_staff
        new_admin.is_superuser = is_superuser
        new_admin.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action_type='ADMIN_CREATE',
            description=f"Admin menambahkan admin baru: {new_admin.username}"
        )
        
        return JsonResponse({
            'status': True,
            'message': f'Admin "{new_admin.username}" berhasil ditambahkan!',
            'data': {
                'id': new_admin.id,
                'username': new_admin.username,
                'email': new_admin.email,
                'is_staff': new_admin.is_staff,
                'is_superuser': new_admin.is_superuser,
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': False,
            'message': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


@csrf_exempt
def api_edit_admin(request, admin_id):
    """API untuk mengedit admin (untuk Flutter)"""
    if request.method != 'POST':
        return JsonResponse({
            'status': False,
            'message': 'Method tidak diizinkan.'
        }, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': False,
            'message': 'Anda harus login terlebih dahulu.'
        }, status=401)
    
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({
            'status': False,
            'message': 'Anda tidak memiliki akses.'
        }, status=403)
    
    try:
        target_admin = User.objects.get(pk=admin_id)
        
        # Tidak bisa edit diri sendiri
        if target_admin.id == request.user.id:
            return JsonResponse({
                'status': False,
                'message': 'Anda tidak dapat mengedit akun Anda sendiri.'
            }, status=403)
        
        data = json.loads(request.body)
        
        # Update fields
        if 'username' in data and data['username']:
            if User.objects.filter(username=data['username']).exclude(pk=admin_id).exists():
                return JsonResponse({
                    'status': False,
                    'message': 'Username sudah digunakan.'
                }, status=400)
            target_admin.username = data['username']
        
        if 'email' in data:
            if data['email'] and User.objects.filter(email=data['email']).exclude(pk=admin_id).exists():
                return JsonResponse({
                    'status': False,
                    'message': 'Email sudah digunakan.'
                }, status=400)
            target_admin.email = data['email']
        
        if 'password' in data and data['password']:
            target_admin.set_password(data['password'])
        
        if 'is_staff' in data:
            target_admin.is_staff = data['is_staff']
        
        if 'is_superuser' in data:
            target_admin.is_superuser = data['is_superuser']
        
        target_admin.save()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action_type='ADMIN_UPDATE',
            description=f"Admin memperbarui admin: {target_admin.username}"
        )
        
        return JsonResponse({
            'status': True,
            'message': f'Admin "{target_admin.username}" berhasil diperbarui!',
            'data': {
                'id': target_admin.id,
                'username': target_admin.username,
                'email': target_admin.email,
                'is_staff': target_admin.is_staff,
                'is_superuser': target_admin.is_superuser,
            }
        }, status=200)
        
    except User.DoesNotExist:
        return JsonResponse({
            'status': False,
            'message': 'Admin tidak ditemukan.'
        }, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': False,
            'message': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


@csrf_exempt
def api_delete_admin(request, admin_id):
    """API untuk menghapus admin (untuk Flutter)"""
    if request.method != 'POST':
        return JsonResponse({
            'status': False,
            'message': 'Method tidak diizinkan.'
        }, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': False,
            'message': 'Anda harus login terlebih dahulu.'
        }, status=401)
    
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({
            'status': False,
            'message': 'Anda tidak memiliki akses.'
        }, status=403)
    
    try:
        target_admin = User.objects.get(pk=admin_id)
        
        # Tidak bisa hapus diri sendiri
        if target_admin.id == request.user.id:
            return JsonResponse({
                'status': False,
                'message': 'Anda tidak dapat menghapus akun Anda sendiri.'
            }, status=403)
        
        admin_username = target_admin.username
        target_admin.delete()
        
        # Log activity
        ActivityLog.objects.create(
            user=request.user,
            action_type='ADMIN_DELETE',
            description=f"Admin menghapus admin: {admin_username}"
        )
        
        return JsonResponse({
            'status': True,
            'message': f'Admin "{admin_username}" berhasil dihapus!'
        }, status=200)
        
    except User.DoesNotExist:
        return JsonResponse({
            'status': False,
            'message': 'Admin tidak ditemukan.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': False,
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)