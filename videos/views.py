from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from .models import Video, Sport, Comment, VideoRating, VideoLike, VideoBookmark

def video_gallery(request):
    videos = Video.objects.all()
    sports = Sport.objects.all()
    
    # Filter by sport
    sport_filter = request.GET.get('sport')
    if sport_filter:
        videos = videos.filter(sport_id=sport_filter)
    
    # Filter by difficulty
    difficulty_filter = request.GET.get('difficulty')
    if difficulty_filter:
        videos = videos.filter(difficulty=difficulty_filter)
    
    # Sorting
    sort_by = request.GET.get('sort', 'popular')
    if sort_by == 'rating':
        videos = videos.annotate(avg_rating=Avg('ratings__rating')).order_by('-avg_rating')
    elif sort_by == 'newest':
        videos = videos.order_by('-created_at')
    elif sort_by == 'shortest':
        videos = videos.order_by('duration')
    else:  # popular (default)
        videos = videos.order_by('-views_count')
    
    context = {
        'videos': videos,
        'sports': sports,
    }
    return render(request, 'videos/video_gallery.html', context)

def video_detail(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    
    # Increment view count
    video.views_count += 1
    video.save()
    
    # Get comments
    comments = video.comments.all()
    sort_comments = request.GET.get('sort_comments', 'latest')
    if sort_comments == 'rating':
        comments = comments.order_by('-rating')
    elif sort_comments == 'helpful':
        comments = comments.order_by('-helpful_count')
    
    # Get rating distribution
    rating_distribution = []
    for stars in range(5, 0, -1):
        count = video.ratings.filter(rating=stars).count()
        percentage = (count / video.ratings_count * 100) if video.ratings_count > 0 else 0
        rating_distribution.append({
            'stars': stars,
            'count': count,
            'percentage': percentage
        })
    
    # Get related videos (same sport, different video)
    related_videos = Video.objects.filter(sport=video.sport).exclude(id=video.id)[:4]
    
    context = {
        'video': video,
        'comments': comments,
        'rating_distribution': rating_distribution,
        'related_videos': related_videos,
    }
    return render(request, 'videos/video_detail.html', context)

@login_required
def add_comment(request, video_id):
    if request.method == 'POST':
        video = get_object_or_404(Video, id=video_id)
        comment_text = request.POST.get('comment')
        rating = request.POST.get('rating')
        
        # Create comment
        Comment.objects.create(
            video=video,
            user=request.user,
            text=comment_text,
            rating=int(rating) if rating else None
        )
        
        # Create or update rating
        if rating:
            VideoRating.objects.update_or_create(
                video=video,
                user=request.user,
                defaults={'rating': int(rating)}
            )
    
    return redirect('videos:detail', video_id=video_id)

@login_required
def like_video(request, video_id):
    if request.method == 'POST':
        video = get_object_or_404(Video, id=video_id)
        VideoLike.objects.get_or_create(video=video, user=request.user)
    return redirect('videos:detail', video_id=video_id)

@login_required
def bookmark_video(request, video_id):
    if request.method == 'POST':
        video = get_object_or_404(Video, id=video_id)
        VideoBookmark.objects.get_or_create(video=video, user=request.user)
    return redirect('videos:detail', video_id=video_id)

@login_required
def helpful_comment(request, comment_id):
    if request.method == 'POST':
        comment = get_object_or_404(Comment, id=comment_id)
        comment.helpful_count += 1
        comment.save()
    return redirect('videos:detail', video_id=comment.video.id)