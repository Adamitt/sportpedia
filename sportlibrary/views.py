import json
from pathlib import Path
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Sport, Rule, Technique, Video, Gear, Bookmark, SportProgress

# =========================
# Import data dari JSON
# =========================
def import_sports_from_json():
    """Import data olahraga dari file JSON tanpa mengubah database fixture"""
    file_path = Path(__file__).resolve().parent / 'database/sports.json'
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for item in data:
        sport, created = Sport.objects.get_or_create(
            id=item.get('id'),
            defaults={
                'name': item.get('name'),
                'category': item.get('category').lower(),
                'difficulty': item.get('difficulty').lower(),
                'description': item.get('description', ''),
                'history': item.get('history', ''),
                'benefits': item.get('benefits', []),
                'popular_countries': item.get('popular_countries', []),
                'tags': item.get('tags', []),
                'is_active': True
            }
        )
        
        # Rules
        for idx, rule_text in enumerate(item.get('rules', []), start=1):
            Rule.objects.get_or_create(
                sport=sport,
                order=idx,
                defaults={'rule_text': rule_text}
            )
        
        # Techniques
        for idx, tech_text in enumerate(item.get('techniques', []), start=1):
            Technique.objects.get_or_create(
                sport=sport,
                order=idx,
                defaults={'technique_name': tech_text, 'description': tech_text}
            )

# =========================
# Views Utama
# =========================
def index(request):
    """Halaman utama pustaka olahraga dengan filter kategori & difficulty"""
    sports = Sport.objects.filter(is_active=True)
    
    # Filter kategori & difficulty
    category = request.GET.get('category', '')
    difficulty = request.GET.get('difficulty', '')
    if category:
        sports = sports.filter(category__iexact=category)
    if difficulty:
        sports = sports.filter(difficulty__iexact=difficulty)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        sports = sports.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(sports, 12)
    page_number = request.GET.get('page')
    sports_page = paginator.get_page(page_number)
    
    context = {
        'sports': sports_page,
        'categories': Sport.CATEGORY_CHOICES,
        'difficulties': Sport.DIFFICULTY_CHOICES,
        'selected_category': category,
        'selected_difficulty': difficulty,
        'search_query': search_query,
    }

    return render(request, 'index.html', context)


def search_sports(request):
    """Search olahraga dengan filter kategori & difficulty"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    difficulty = request.GET.get('difficulty', '')
    
    sports = Sport.objects.filter(is_active=True)
    
    if query:
        sports = sports.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(history__icontains=query) |
            Q(tags__icontains=query)
        )
    if category:
        sports = sports.filter(category__iexact=category)
    if difficulty:
        sports = sports.filter(difficulty__iexact=difficulty)
    
    paginator = Paginator(sports, 12)
    page_number = request.GET.get('page')
    sports_page = paginator.get_page(page_number)
    
    context = {
        'sports': sports_page,
        'query': query,
        'selected_category': category,
        'selected_difficulty': difficulty,
        'categories': Sport.CATEGORY_CHOICES,
        'difficulties': Sport.DIFFICULTY_CHOICES,
    }
    
    return render(request, 'sportlibrary/search_results.html', context)


@login_required
def toggle_bookmark(request, sport_id):
    sport = get_object_or_404(Sport, id=sport_id)
    bookmark, created = Bookmark.objects.get_or_create(user=request.user, sport=sport)
    
    if not created:
        bookmark.delete()
        bookmarked = False
        messages.success(request, f'{sport.name} dihapus dari bookmark')
    else:
        bookmarked = True
        messages.success(request, f'{sport.name} ditambahkan ke bookmark')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'bookmarked': bookmarked,
            'message': f'{sport.name} {"ditambahkan ke" if bookmarked else "dihapus dari"} bookmark'
        })
    
    return redirect('sport_detail', sport_id=sport_id)


@login_required
def bookmark_list(request):
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('sport')
    return render(request, 'sportlibrary/bookmark_list.html', {'bookmarks': bookmarks})


@login_required
def update_bookmark_notes(request, bookmark_id):
    if request.method == 'POST':
        bookmark = get_object_or_404(Bookmark, id=bookmark_id, user=request.user)
        bookmark.notes = request.POST.get('notes', '')
        bookmark.save()
        messages.success(request, 'Catatan berhasil diperbarui')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Catatan berhasil diperbarui'})
    return redirect('sportlibrary:bookmark_list')


@login_required
def mark_video_complete(request, video_id):
    if request.method == 'POST':
        video = get_object_or_404(Video, id=video_id)
        sport = video.sport
        progress, created = SportProgress.objects.get_or_create(user=request.user, sport=sport)
        
        if video in progress.completed_videos.all():
            progress.completed_videos.remove(video)
            completed = False
        else:
            progress.completed_videos.add(video)
            completed = True
        
        total_videos = sport.videos.count()
        if total_videos > 0:
            progress.progress_percentage = int((progress.completed_videos.count() / total_videos) * 100)
            progress.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'completed': completed,
                'progress_percentage': progress.progress_percentage,
                'message': 'Video ditandai sebagai ' + ('selesai' if completed else 'belum selesai')
            })
        
        messages.success(request, f'Video ditandai sebagai {"selesai" if completed else "belum selesai"}')
        return redirect('sportlibrary:sport_detail', sport_id=sport.id)
    
    return redirect('sportlibrary:index')


@login_required
def my_progress(request):
    progress_list = SportProgress.objects.filter(user=request.user).select_related('sport')
    sort_by = request.GET.get('sort', 'last_accessed')
    if sort_by == 'progress':
        progress_list = progress_list.order_by('-progress_percentage', '-last_accessed')
    else:
        progress_list = progress_list.order_by('-last_accessed')
    
    return render(request, 'sportlibrary/my_progress.html', {'progress_list': progress_list, 'sort_by': sort_by})


def sport_by_category(request, category):
    sports = Sport.objects.filter(is_active=True, category__iexact=category)
    context = {
        'sports': sports,
        'category': category,
        'category_display': dict(Sport.CATEGORY_CHOICES).get(category.lower(), category),
    }
    return render(request, 'sportlibrary/sport_by_category.html', context)


def gear_detail(request, gear_id):
    gear = get_object_or_404(Gear, id=gear_id)
    return render(request, 'sportlibrary/gear_detail.html', {
        'gear': gear,
        'brands': gear.get_brands_list(),
        'materials': gear.get_materials_list(),
        'tags': gear.get_tags_list(),
    })


def video_list(request, sport_id):
    sport = get_object_or_404(Sport, id=sport_id)
    videos = sport.videos.all()
    completed_video_ids = []
    if request.user.is_authenticated:
        try:
            progress = SportProgress.objects.get(user=request.user, sport=sport)
            completed_video_ids = list(progress.completed_videos.values_list('id', flat=True))
        except SportProgress.DoesNotExist:
            pass
    return render(request, 'sportlibrary/video_list.html', {
        'sport': sport,
        'videos': videos,
        'completed_video_ids': completed_video_ids
    })


def popular_sports(request):
    sports = Sport.objects.filter(is_active=True).annotate(
        bookmark_count=Count('bookmarked_by')
    ).order_by('-bookmark_count')[:20]
    return render(request, 'sportlibrary/popular_sports.html', {'sports': sports, 'title': 'Olahraga Populer'})

def index(request):
    sports = Sport.objects.filter(is_active=True)
    
    # Filter kategori & difficulty
    category = request.GET.get('category')
    difficulty = request.GET.get('difficulty')
    search_query = request.GET.get('search')

    if category:
        sports = sports.filter(category=category)
    if difficulty:
        sports = sports.filter(difficulty=difficulty)
    if search_query:
        sports = sports.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(sports, 12)
    page_number = request.GET.get('page')
    sports_page = paginator.get_page(page_number)

    # Bookmark user
    bookmarked_ids = []
    if request.user.is_authenticated:
        bookmarked_ids = list(
            Bookmark.objects.filter(user=request.user, sport__in=sports_page).values_list('sport_id', flat=True)
        )

    context = {
        'sports': sports_page,
        'categories': Sport.CATEGORY_CHOICES,
        'difficulties': Sport.DIFFICULTY_CHOICES,
        'selected_category': category,
        'selected_difficulty': difficulty,
        'search_query': search_query,
        'bookmarked_ids': bookmarked_ids,
    }

    return render(request, 'index.html', context)

@login_required
def sport_detail(request, sport_id):
    """
    Halaman detail olahraga
    Menampilkan: 
      - Info olahraga (nama, kategori, difficulty, history, benefits, tags)
      - Rules
      - Techniques
      - Video list (link ke video_list)
      - Tombol bookmark / toggle
    """
    sport = get_object_or_404(Sport, id=sport_id)
    
    # Ambil rules dan techniques
    rules = sport.rules.order_by('order')  # asumsi related_name='rules'
    techniques = sport.techniques.order_by('order')  # asumsi related_name='techniques'
    
    # Bookmark status
    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = Bookmark.objects.filter(user=request.user, sport=sport).exists()
    
    # Video count untuk progress
    total_videos = sport.videos.count()
    completed_count = 0
    progress_percentage = 0
    if request.user.is_authenticated:
        try:
            progress = SportProgress.objects.get(user=request.user, sport=sport)
            completed_count = progress.completed_videos.count()
            if total_videos > 0:
                progress_percentage = int((completed_count / total_videos) * 100)
        except SportProgress.DoesNotExist:
            pass

    context = {
        'sport': sport,
        'rules': rules,
        'techniques': techniques,
        'is_bookmarked': is_bookmarked,
        'total_videos': total_videos,
        'completed_count': completed_count,
        'progress_percentage': progress_percentage,
    }

    return render(request, 'sportlibrary/sport_detail.html', context)

# =========================
# API Endpoints
# =========================
@login_required
def api_bookmark_status(request, sport_id):
    is_bookmarked = Bookmark.objects.filter(user=request.user, sport_id=sport_id).exists()
    return JsonResponse({'is_bookmarked': is_bookmarked})


@login_required
def api_progress_status(request, sport_id):
    try:
        progress = SportProgress.objects.get(user=request.user, sport_id=sport_id)
        return JsonResponse({
            'exists': True,
            'progress_percentage': progress.progress_percentage,
            'completed_videos_count': progress.completed_videos.count(),
        })
    except SportProgress.DoesNotExist:
        return JsonResponse({'exists': False})
