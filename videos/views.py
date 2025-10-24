import json
import os
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from datetime import datetime
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Video
from .forms import VideoForm


# Path ke file JSON
JSON_FILE = os.path.join(settings.BASE_DIR, 'videos', 'data', 'videos.json')
COMMENTS_FILE = os.path.join(settings.BASE_DIR, 'videos', 'data', 'comments.json')
BOOKMARKS_FILE = os.path.join(settings.BASE_DIR, 'videos', 'data', 'bookmarks.json')

# Sport mapping
SPORT_MAPPING = {
    1: "Badminton",
    2: "Yoga", 
    3: "Tennis",
    4: "Swimming",
    5: "Archery",
    6: "Basketball",
    7: "Football",
    8: "Futsal",
    9: "Cycling",
    10: "Table Tennis",
    11: "Volleyball",
    12: "Rock Climbing",
    13: "Muay Thai",
    14: "Golf",
    15: "Surfing",
    16: "Pencak Silat",
    17: "Baseball",
    18: "Skateboarding",
    19: "Calisthenics",
    20: "Wall Climbing"
}

def load_videos():
    """Load video data from JSON file"""
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_videos(videos):
    """Save video data to JSON file"""
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)

def load_comments():
    """Load comments data from JSON file"""
    try:
        with open(COMMENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_comments(comments):
    """Save comments data to JSON file"""
    os.makedirs(os.path.dirname(COMMENTS_FILE), exist_ok=True)
    with open(COMMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(comments, f, indent=2, ensure_ascii=False)

def load_bookmarks():
    """Load bookmarks data from JSON file"""
    try:
        with open(BOOKMARKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_bookmarks(bookmarks):
    """Save bookmarks data to JSON file"""
    os.makedirs(os.path.dirname(BOOKMARKS_FILE), exist_ok=True)
    with open(BOOKMARKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(bookmarks, f, indent=2, ensure_ascii=False)

def video_gallery(request):
    """Display video gallery with filters and search"""
    videos = load_videos()
    
    # Get unique sports for filter (from sportlibrary if needed)
    sports = []
    sport_mapping = {}
    try:
        from sportlibrary.models import Sport as SportModel
        sports = SportModel.objects.all()
        # Create mapping dict for sport_id -> sport_name
        sport_mapping = {sport.id: sport.name for sport in sports}
    except:
        pass
    
    # Use hardcoded mapping as fallback
    if not sport_mapping:
        sport_mapping = SPORT_MAPPING
        # Create sports list for filter dropdown
        sports = [{'id': sid, 'name': name} for sid, name in SPORT_MAPPING.items()]
    
    # Add sport_name to each video
    for video in videos:
        video['sport_name'] = sport_mapping.get(video['sport_id'], f'Sport {video["sport_id"]}')
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        videos = [v for v in videos if 
                  search_query.lower() in v['title'].lower() or 
                  search_query.lower() in v['description'].lower() or
                  search_query.lower() in v.get('instructor', '').lower() or
                  any(search_query.lower() in tag.lower() for tag in v.get('tags', []))]
    
    # Filter by sport
    sport_filter = request.GET.get('sport')
    if sport_filter:
        videos = [v for v in videos if str(v['sport_id']) == sport_filter]
    
    # Filter by difficulty
    difficulty_filter = request.GET.get('difficulty')
    difficulty_map = {
        'beginner': 'Pemula',
        'intermediate': 'Menengah',
        'advanced': 'Lanjutan'
    }
    if difficulty_filter and difficulty_filter in difficulty_map:
        videos = [v for v in videos if v['difficulty'] == difficulty_map[difficulty_filter]]
    
    # Sorting
    sort_by = request.GET.get('sort', 'popular')
    if sort_by == 'rating':
        videos = sorted(videos, key=lambda x: x.get('rating', 0), reverse=True)
    elif sort_by == 'newest':
        videos = sorted(videos, key=lambda x: x.get('upload_date', ''), reverse=True)
    elif sort_by == 'shortest':
        videos = sorted(videos, key=lambda x: x.get('duration', '99:99'))
    else:  # popular (default)
        videos = sorted(videos, key=lambda x: x.get('views', 0), reverse=True)
    
    context = {
        'videos': videos,
        'sports': sports,
        'search_query': search_query,
    }
    return render(request, 'videos/video_gallery.html', context)

def staff_required(user):
    return user.is_staff


@login_required
@user_passes_test(staff_required)
def video_create(request):
    form = VideoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Video berhasil ditambahkan! 🎥")
        return redirect('videos:video_gallery')
    return render(request, 'videos/video_create.html', {'form': form})


@login_required
@user_passes_test(staff_required)
def video_update(request, video_id):
    video = get_object_or_404(Video, pk=video_id)
    form = VideoForm(request.POST or None, instance=video)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Video berhasil diperbarui! ✏️")
        return redirect('videos:video_detail', video_id=video.id)
    return render(request, 'videos/video_update.html', {'form': form, 'video': video})


@login_required
@user_passes_test(staff_required)
def video_delete(request, video_id):
    video = get_object_or_404(Video, pk=video_id)
    if request.method == "POST":
        video.delete()
        messages.success(request, "Video berhasil dihapus! 🗑️")
        return redirect('videos:video_gallery')
    return render(request, 'videos/video_confirm_delete.html', {'video': video})

def video_detail(request, video_id):
    """Display video detail"""
    videos = load_videos()
    
    # Find video by ID
    video = next((v for v in videos if v['id'] == video_id), None)
    
    if not video:
        messages.error(request, 'Video not found')
        return redirect('videos:video_gallery')
    
    # Add sport_name to video
    try:
        from sportlibrary.models import Sport as SportModel
        sport = SportModel.objects.filter(id=video['sport_id']).first()
        video['sport_name'] = sport.name if sport else SPORT_MAPPING.get(video['sport_id'], f'Sport {video["sport_id"]}')
    except:
        video['sport_name'] = SPORT_MAPPING.get(video['sport_id'], f'Sport {video["sport_id"]}')
    
    # Increment view count
    video['views'] = video.get('views', 0) + 1
    
    # Save updated views
    for idx, v in enumerate(videos):
        if v['id'] == video_id:
            videos[idx] = video
            break
    save_videos(videos)
    
    # Get related videos (same sport, different video)
    related_videos = [v for v in videos if v['sport_id'] == video['sport_id'] and v['id'] != video_id][:4]
    
    # Add sport_name to related videos
    try:
        from sportlibrary.models import Sport as SportModel
        sport_mapping = {sport.id: sport.name for sport in SportModel.objects.all()}
        if not sport_mapping:
            sport_mapping = SPORT_MAPPING
    except:
        sport_mapping = SPORT_MAPPING
        
    for rv in related_videos:
        rv['sport_name'] = sport_mapping.get(rv['sport_id'], f'Sport {rv["sport_id"]}')
    
    # Load comments for this video
    all_comments = load_comments()
    comments = [c for c in all_comments if c['video_id'] == video_id]
    
    # Check if video is bookmarked by user
    bookmarks = load_bookmarks()
    username = request.user.username if request.user.is_authenticated else 'anonymous'
    is_bookmarked = any(b['video_id'] == video_id and b['user'] == username for b in bookmarks)
    
    # Mock ratings for display
    rating_distribution = [
        {'stars': 5, 'count': 186, 'percentage': 75},
        {'stars': 4, 'count': 49, 'percentage': 20},
        {'stars': 3, 'count': 8, 'percentage': 3},
        {'stars': 2, 'count': 3, 'percentage': 1},
        {'stars': 1, 'count': 2, 'percentage': 1},
    ]
    
    context = {
        'video': video,
        'comments': comments,
        'rating_distribution': rating_distribution,
        'related_videos': related_videos,
        'is_bookmarked': is_bookmarked,
    }
    return render(request, 'videos/video_detail.html', context)

@login_required
def add_comment(request, video_id):
    if request.method == "POST":
        comment_text = request.POST.get("comment", "").strip()
        username = request.user.username
        if not comment_text:
            return JsonResponse({'success': False, 'message': 'Komentar kosong.'})
        new_comment = {
            'id': int(datetime.now().timestamp()),
            'user': username,
            'text': comment_text,
            'helpful_count': 0,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        comments = request.session.get('comments', [])
        comments.insert(0, new_comment)
        request.session['comments'] = comments
        return JsonResponse({'success': True, 'comment': new_comment})
    return JsonResponse({'success': False})

@login_required
def like_video(request, video_id):
    videos = load_videos()
    video = next((v for v in videos if v['id'] == video_id), None)
    if not video:
        return JsonResponse({'success': False})
    video['likes'] = video.get('likes', 0) + 1
    save_videos(videos)
    return JsonResponse({'success': True, 'likes': video['likes']})

@login_required
def bookmark_video(request, video_id):
    bookmarks = request.session.get('bookmarks', [])
    if video_id in bookmarks:
        bookmarks.remove(video_id)
        request.session['bookmarks'] = bookmarks
        return JsonResponse({'success': True, 'bookmarked': False})
    bookmarks.append(video_id)
    request.session['bookmarks'] = bookmarks
    return JsonResponse({'success': True, 'bookmarked': True})


def helpful_comment(request, comment_id):
    """Mark comment as helpful"""
    if request.method == 'POST':
        comments = load_comments()
        
        # Find comment by ID
        comment = next((c for c in comments if c['id'] == comment_id), None)
        
        if not comment:
            return JsonResponse({'success': False, 'error': 'Comment not found'}, status=404)
        
        # Increment helpful count
        comment['helpful'] = comment.get('helpful', 0) + 1
        
        # Save updated comments
        for idx, c in enumerate(comments):
            if c['id'] == comment_id:
                comments[idx] = comment
                break
        save_comments(comments)
        
        return JsonResponse({
            'success': True, 
            'helpful': comment['helpful']
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

# CRUD Operations

def video_create(request):
    """Create new video"""
    if request.method == 'POST':
        videos = load_videos()
        
        # Get new ID
        new_id = max([v['id'] for v in videos]) + 1 if videos else 1
        
        # Create new video
        new_video = {
            'id': new_id,
            'sport_id': int(request.POST.get('sport_id', 1)),
            'title': request.POST.get('title'),
            'difficulty': request.POST.get('difficulty', 'Pemula'),
            'duration': request.POST.get('duration'),
            'url': request.POST.get('url'),
            'thumbnail': request.POST.get('thumbnail', ''),
            'instructor': request.POST.get('instructor', 'Admin'),
            'description': request.POST.get('description', ''),
            'rating': 0.0,
            'views': 0,
            'likes': 0,
            'upload_date': '2025-10-23',
            'tags': [tag.strip() for tag in request.POST.get('tags', '').split(',') if tag.strip()]
        }
        
        videos.append(new_video)
        save_videos(videos)
        
        messages.success(request, 'Video created successfully!')
        return redirect('videos:video_detail', video_id=new_id)
    
    return render(request, 'videos/video_form.html')

def video_update(request, video_id):
    """Update existing video"""
    videos = load_videos()
    video = next((v for v in videos if v['id'] == video_id), None)
    
    if not video:
        messages.error(request, 'Video not found')
        return redirect('videos:video_gallery')
    
    if request.method == 'POST':
        # Update video data
        video['title'] = request.POST.get('title')
        video['description'] = request.POST.get('description')
        video['sport_id'] = int(request.POST.get('sport_id'))
        video['difficulty'] = request.POST.get('difficulty')
        video['duration'] = request.POST.get('duration')
        video['url'] = request.POST.get('url')
        video['thumbnail'] = request.POST.get('thumbnail', video.get('thumbnail', ''))
        video['instructor'] = request.POST.get('instructor', video.get('instructor', ''))
        video['tags'] = [tag.strip() for tag in request.POST.get('tags', '').split(',') if tag.strip()]
        
        # Save updated videos
        for idx, v in enumerate(videos):
            if v['id'] == video_id:
                videos[idx] = video
                break
        save_videos(videos)
        
        messages.success(request, 'Video updated successfully!')
        return redirect('videos:video_detail', video_id=video_id)
    
    context = {'video': video}
    return render(request, 'videos/video_form.html', context)

def video_delete(request, video_id):
    """Delete video"""
    if request.method == 'POST':
        videos = load_videos()
        videos = [v for v in videos if v['id'] != video_id]
        save_videos(videos)
        
        messages.success(request, 'Video deleted successfully!')
        return redirect('videos:video_gallery')
    
    return redirect('videos:video_gallery')