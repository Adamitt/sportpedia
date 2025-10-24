import json
from django.conf import settings
from django.http import HttpResponseNotFound
from django.shortcuts import render
from django.urls import reverse
from metrics.utils import bump_view

def _load_sports_json():
    data_path = settings.BASE_DIR / 'database' / 'sports.json'
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def _normalize_id(raw_id: str):
    """
    Terima:
      - "10"  -> 10
      - "00000000-0000-0000-0000-00000000000a" -> 10 (ambil segmen hex terakhir)
      - "00000000-0000-0000-0000-000000000003" -> 3
    Kalau gagal parse, balikin None.
    """
    s = str(raw_id).strip().lower()
    # angka murni?
    if s.isdigit():
        try:
            return int(s)
        except Exception:
            return None
    # kemungkinan UUID-like: ambil segmen terakhir setelah '-'
    if '-' in s:
        tail = s.split('-')[-1]  # contoh: '00000000000a'
        try:
            return int(tail, 16)
        except Exception:
            return None
    # terakhir: coba hex langsung (tanpa '-')
    try:
        return int(s, 16)
    except Exception:
        return None

def show_sports(request):
    sports = _load_sports_json()
    return render(request, 'sportlibrary/sportlibrary.html', {"sports": sports})

def sport_detail(request, sport_id):
    sports = _load_sports_json()

    normalized = _normalize_id(sport_id)
    # fallback: juga coba match string persis kalau ada yang menyimpan sebagai string
    sport = None
    if normalized is not None:
        sport = next((s for s in sports if str(s.get('id')) == str(normalized) or s.get('id') == normalized), None)
    if sport is None:
        sport = next((s for s in sports if str(s.get('id')) == str(sport_id)), None)

    if not sport:
        # gak usah render 404.html biar gak error template
        return HttpResponseNotFound("⚠️ Sport tidak ditemukan.")

    # Catat view untuk What's Hot
    url   = reverse('sportlibrary:sport_detail', kwargs={'sport_id': str(sport_id)})
    title = sport.get('name') or f"Sport #{sport.get('id')}"
    image = sport.get('image') or sport.get('thumbnail') or ""
    key   = f"sportjson:{sport.get('id')}"
    bump_view(key, title=title, url=url, category="Library", image=image, request=request)

    return render(request, 'sportlibrary/detail.html', {"sport": sport})

def saved_sports(request):
    all_sports = _load_sports_json()
    return render(request, 'bookmarklist.html', {"all_sports_json": json.dumps(all_sports)})
