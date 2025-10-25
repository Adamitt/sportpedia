from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from gearguide.models import Gear
from sportlibrary.models import Sport
from profile_app.models import ActivityLog
from django.db import models
import json
from pathlib import Path

# only admin/staff
def admin_only(user):
    return user.is_staff or user.is_superuser

@user_passes_test(admin_only, login_url='/accounts/login/')
def dashboard(request):
    """Halaman utama dashboard admin"""
    total_gears = Gear.objects.count()
    total_sports = Sport.objects.count()

    return render(request, 'dashboard/dashboard.html', {
        'total_gears': total_gears,
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