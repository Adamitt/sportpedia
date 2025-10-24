from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from gearguide.models import Gear
from sportlibrary.models import Sport
from profile_app.models import ActivityLog
from django.contrib.auth.models import User # Import User model
from django.db.models import Q            # For OR queries
from .forms import AdminUserCreationForm, AdminUserChangeForm # Import the new forms
from django.views.decorators.http import require_POST # For delete safety
from django.http import JsonResponse

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
        # Basic fields
        name = request.POST.get('name')
        category = request.POST.get('category')
        difficulty = request.POST.get('difficulty')
        description = request.POST.get('description')
        history = request.POST.get('history')

        # Process JSONFields (assuming comma-separated input in textareas)
        rules_str = request.POST.get('rules', '')
        techniques_str = request.POST.get('techniques', '')
        benefits_str = request.POST.get('benefits', '')
        countries_str = request.POST.get('popular_countries', '')
        tags_str = request.POST.get('tags', '')

        def parse_json_list(text):
            if not text: return []
            return [item.strip() for item in text.split(',') if item.strip()]

        try:
            Sport.objects.create(
                name=name,
                category=category,
                difficulty=difficulty,
                description=description,
                history=history,
                rules=parse_json_list(rules_str),
                techniques=parse_json_list(techniques_str),
                benefits=parse_json_list(benefits_str),
                popular_countries=parse_json_list(countries_str),
                tags=parse_json_list(tags_str),
            )
            messages.success(request, f'✅ Olahraga "{name}" berhasil ditambahkan!')
            return redirect('admin_sportpedia:manage_library')
        except Exception as e:
            messages.error(request, f'❌ Gagal menambahkan olahraga: {e}')
            return render(request, 'library_app/sport_form.html', {'edit_mode': False})

    return render(request, 'library_app/sport_form.html', {'edit_mode': False})

@user_passes_test(admin_only, login_url='/accounts/login/')
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
             return render(request, 'library_app/sport_form.html', {'sport': sport, 'edit_mode': True})

    context = {
        'sport': sport,
        'edit_mode': True,
        'rules_str': ', '.join(sport.rules),
        'techniques_str': ', '.join(sport.techniques),
        'benefits_str': ', '.join(sport.benefits),
        'countries_str': ', '.join(sport.popular_countries),
        'tags_str': ', '.join(sport.tags),
    }
    return render(request, 'library_app/sport_form.html', context)

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

@user_passes_test(admin_only, login_url='/accounts/login/')
@require_POST
def delete_admin(request, admin_id):
    """Menangani POST delete (non-AJAX, me-reload halaman)."""
    target_admin = get_object_or_404(User, pk=admin_id)
    target_username = target_admin.username
    if target_admin == request.user:
        messages.error(request, '❌ Anda tidak dapat menghapus akun Anda sendiri.')
        return redirect('admin_sportpedia:manage_admin')
    try:
        target_admin.delete()
        ActivityLog.objects.create(
            user=request.user, action_type='ADMIN_DELETE',
            description=f"Admin menghapus admin: {target_username}"
        )
        messages.success(request, f'🗑️ Admin "{target_username}" berhasil dihapus!')
    except Exception as e:
        messages.error(request, f'❌ Gagal menghapus admin: {e}')
    return redirect('admin_sportpedia:manage_admin')