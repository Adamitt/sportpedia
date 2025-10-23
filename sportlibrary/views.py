from django.shortcuts import render
import json
from pathlib import Path
from django.urls import reverse #
from metrics.utils import bump_view #
from django.conf import settings #


def show_sports(request):
    data_path = settings.BASE_DIR / 'database' / 'sports.json'


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
    ##
    key   = f"sportjson:{sport_id}"
    url   = reverse('sportlibrary:sport_detail', kwargs={'sport_id': sport_id})
    title = sport.get('name') or f"Sport #{sport_id}"
    image = sport.get('image') or sport.get('thumbnail') or ""
    bump_view(key, title=title, url=url, category="Library", image=image, request=request)

    return render(request, 'sportlibrary/detail.html', context)

def saved_sports(request):
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / 'database' / 'sports.json'
    
    with open(data_path, 'r', encoding='utf-8') as file:
        all_sports = json.load(file)
    
    context = {"all_sports_json": json.dumps(all_sports)}
    return render(request, 'bookmarklist.html', context)