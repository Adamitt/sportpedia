from django.shortcuts import render
import json
from pathlib import Path

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

    context = {"sport": sport}
    return render(request, 'sportlibrary/detail.html', context)

def saved_sports(request):
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / 'database' / 'sports.json'
    
    with open(data_path, 'r', encoding='utf-8') as file:
        all_sports = json.load(file)
    
    context = {"all_sports_json": json.dumps(all_sports)}
    return render(request, 'sportlibrary/saved.html', context)