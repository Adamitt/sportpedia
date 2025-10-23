from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from gearguide.models import Gear
from sportlibrary.models import Sport

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
