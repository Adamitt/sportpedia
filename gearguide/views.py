from django.shortcuts import render
from .models import Gear

def show_all_gears(request):
    gears = Gear.objects.all()
    context = {
        'title': 'Direktori Perlengkapan',
        'gears': gears
    }
    return render(request, 'gearguide/all_gears.html', context)

def show_gears_by_sport(request, sport_name):
    gears = Gear.objects.filter(sport__name=sport_name)
    context = {
        'title': f'Perlengkapan untuk {sport_name}',
        'gears': gears
    }
    return render(request, 'gearguide/all_gears.html', context)
