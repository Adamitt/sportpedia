import json
from pathlib import Path
from django.shortcuts import render, get_object_or_404, redirect
from .models import Gear
from .forms import GearForm  # pastikan forms.py udah ada

def show_gear_detail(request, gear_id):
    gear = get_object_or_404(Gear, id=gear_id)
    context = {
        "title": gear.name,
        "gear": gear,
    }
    return render(request, "gearguide/gear_detail.html", context)

def show_all_gears(request):
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_path = base_dir / 'database' / 'gears.json'

    with open(data_path, 'r', encoding='utf-8') as file:
        gears = json.load(file)

    sports = sorted({g.get("tags", [])[0].capitalize() for g in gears if g.get("tags")})
    sport_filter = request.GET.get('sport')
    level_filter = request.GET.get('level')

    if sport_filter:
        gears = [g for g in gears if sport_filter.lower() in [t.lower() for t in g.get("tags", [])]]
    if level_filter:
        gears = [g for g in gears if g.get("level", "").lower() == level_filter.lower()]

    context = {
        "title": "Gear Guide",
        "gears": gears,
        "sports": sports,
    }
    return render(request, "gearguide/gearguide.html", context)

def card_details(request, gear_id):
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_path = base_dir / 'database' / 'gears.json'

    with open(data_path, 'r', encoding='utf-8') as file:
        gears = json.load(file)

    gear = next((g for g in gears if g['id'] == gear_id), None)
    if not gear:
        return render(request, "404.html", status=404)

    context = {
        "title": gear["name"],
        "gear": gear,
    }
    return render(request, "gearguide/card_details.html", context)

def add_gear(request):
    if request.method == "POST":
        form = GearForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("gearguide:show_all_gears")
    else:
        form = GearForm()

    return render(request, "gearguide/add_gear.html", {"form": form})
