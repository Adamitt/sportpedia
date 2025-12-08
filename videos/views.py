import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.http import JsonResponse, Http404
from django.db.models import F, Q, Avg, Count # <-- Import Avg dan Count
from django.views.decorators.http import require_POST
from django.utils import timezone # Untuk rating/comment

from .models import Video, Comment, VideoBookmark, VideoRating, VideoLike # <-- Import semua model
from .forms import VideoForm # Asumsi Anda punya ini
from sportlibrary.models import Sport
from metrics.utils import bump_view
from profile_app.models import UserProfile

# ==================================
# Helper
# ==================================

def staff_required(user):
    return user.is_staff

# ==================================
# Views Tampilan (READ)
# ==================================

def video_gallery(request):
    """Menampilkan galeri video dari DATABASE"""
    
    videos_qs = Video.objects.select_related('sport', 'uploader').annotate(
        avg_rating=Avg('ratings__rating'),
        like_count=Count('likes')
    )
    
    sports = Sport.objects.all().order_by('name')
    
    # Search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        videos_qs = videos_qs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(instructor__icontains=search_query) | # <-- SEKARANG BERFUNGSI
            Q(tags__icontains=search_query)       # <-- SEKARANG BERFUNGSI
        )

    # Filter by sport
    sport_filter = request.GET.get('sport')
    if sport_filter:
        videos_qs = videos_qs.filter(sport__id=sport_filter)
    
    # Filter by difficulty
    difficulty_filter = request.GET.get('difficulty')
    if difficulty_filter:
        videos_qs = videos_qs.filter(difficulty=difficulty_filter)
    
    # Sorting
    sort_by = request.GET.get('sort', 'popular')
    if sort_by == 'rating':
        # Urutkan berdasarkan anotasi avg_rating
        videos_qs = videos_qs.order_by('-avg_rating', '-views_count') 
    elif sort_by == 'newest':
        videos_qs = videos_qs.order_by('-created_at', '-views_count') # Ganti ke created_at
    elif sort_by == 'shortest':
        videos_qs = videos_qs.order_by('duration')
    else: # popular (default)
        videos_qs = videos_qs.order_by('-views_count')
    
    context = {
        'videos': videos_qs, # Tidak perlu list() jika me-looping di template
        'sports': sports,
        'search_query': search_query,
        'selected_sport': sport_filter,
        'selected_difficulty': difficulty_filter,
        'sort_by': sort_by,
    }
    return render(request, 'videos/video_gallery.html', context)

def video_detail(request, video_id):
    """Menampilkan detail video dari DATABASE"""
    try:
        video = get_object_or_404(Video.objects.select_related('sport', 'uploader'), pk=video_id)
    except Exception:
         raise Http404("Video tidak ditemukan.")

    # Panggil bump_view
    try:
        key = f"video:{video.id}"
        url = reverse('videos:video_detail', kwargs={'video_id': video.id})
        title = video.title
        # --- PERBAIKAN: Gunakan thumbnail_url ---
        image = video.thumbnail_url if video.thumbnail_url else ""
        
        bump_view(key=key, title=title, url=url, category="Video", image=image, request=request)
        
        video.views_count = F('views_count') + 1
        video.save(update_fields=['views_count'])
        video.refresh_from_db() # Ambil nilai views_count terbaru
        
    except Exception as e:
        print(f"Gagal mencatat view untuk video_id {video_id}: {e}")
    
    # Ambil video terkait
    related_videos = Video.objects.filter(sport=video.sport).exclude(pk=video_id).select_related('sport')[:4]
    
    # --- PERBAIKAN: Ambil data nyata dari DB ---
    comments = video.comments.all().select_related('user', 'user__profile')
    is_bookmarked = False
    is_liked = False
    user_rating = None
    
    if request.user.is_authenticated:
        is_bookmarked = VideoBookmark.objects.filter(video=video, user=request.user).exists()
        is_liked = VideoLike.objects.filter(video=video, user=request.user).exists()
        rating_obj = VideoRating.objects.filter(video=video, user=request.user).first()
        if rating_obj:
            user_rating = rating_obj.rating
    # --- SELESAI PERBAIKAN ---

    context = {
        'video': video,
        'related_videos': related_videos,
        'is_bookmarked': is_bookmarked, # Data nyata
        'comments': comments,           # Data nyata
        'user_rating': user_rating,     # Data nyata
    }
    return render(request, 'videos/video_detail.html', context)

# ==================================
# Views Admin (CRUD)
# ==================================

@login_required
@user_passes_test(staff_required)
def video_create(request):
    """Membuat video baru di DATABASE"""
    if request.method == "POST":
        # --- PERBAIKAN: HAPUS request.FILES ---
        form = VideoForm(request.POST) 
        if form.is_valid():
            video = form.save(commit=False)
            video.uploader = request.user
            video.save()
            form.save_m2m() # Wajib untuk M2M, tapi aman untuk form ini
            messages.success(request, "Video berhasil ditambahkan! 🎥")
            return redirect('videos:video_detail', video_id=video.id)
    else:
        form = VideoForm()
    
    context = { 'form': form, 'sports': Sport.objects.all() }
    return render(request, 'videos/video_form.html', context)


@login_required
@user_passes_test(staff_required)
def video_update(request, video_id):
    """Mengupdate video di DATABASE"""
    video = get_object_or_404(Video, pk=video_id)
    if request.method == "POST":
        # --- PERBAIKAN: HAPUS request.FILES ---
        form = VideoForm(request.POST, instance=video) 
        if form.is_valid():
            form.save()
            form.save_m2m()
            messages.success(request, "Video berhasil diperbarui! ✏️")
            return redirect('videos:video_detail', video_id=video.id)
    else:
        form = VideoForm(instance=video)
        
    context = { 'form': form, 'video': video, 'sports': Sport.objects.all() }
    return render(request, 'videos/video_form.html', context)


@login_required
@user_passes_test(staff_required)
@require_POST # Jadikan POST untuk keamanan
def video_delete(request, video_id):
    """Menghapus video dari DATABASE"""
    video = get_object_or_404(Video, pk=video_id)
    video_title = video.title
    video.delete()
    messages.success(request, f"Video '{video_title}' berhasil dihapus! 🗑️")
    return redirect('videos:video_gallery')

# ==================================
# Views Interaksi (AJAX)
# ==================================

@login_required
@require_POST
def like_video(request, video_id):
    """Menangani Like/Unlike video (Toggle)"""
    try:
        video = get_object_or_404(Video, pk=video_id)
        
        like, created = VideoLike.objects.get_or_create(user=request.user, video=video)
        
        if created:
            is_liked = True
            # Update hitungan total di model Video secara atomik
            Video.objects.filter(pk=video_id).update(total_likes=F('total_likes') + 1)
        else:
            like.delete()
            is_liked = False
            # Update hitungan total di model Video secara atomik
            Video.objects.filter(pk=video_id).update(total_likes=F('total_likes') - 1)
            
        # Ambil total likes terbaru
        video.refresh_from_db()
        total_likes = video.total_likes
        
        return JsonResponse({'success': True, 'is_liked': is_liked, 'total_likes': total_likes})
    except Video.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Video not found'}, status=404)

@login_required
@require_POST
def bookmark_video(request, video_id):
    """Menangani Bookmark/Unbookmark video (Toggle)"""
    video = get_object_or_404(Video, pk=video_id)
    
    bookmark, created = VideoBookmark.objects.get_or_create(user=request.user, video=video)
    
    if created:
        return JsonResponse({'success': True, 'bookmarked': True, 'message': 'Video saved'})
    else:
        bookmark.delete()
        return JsonResponse({'success': True, 'bookmarked': False, 'message': 'Video removed'})

@login_required
@require_POST
def add_comment(request, video_id):
    """Menambah komentar baru ke DATABASE (Versi Aman)"""
    video = get_object_or_404(Video, pk=video_id)
    comment_text = request.POST.get("comment", "").strip()
    rating_val = request.POST.get("rating")
    
    if not comment_text:
        return JsonResponse({'success': False, 'message': 'Komentar kosong.'}, status=400)
    
    # Handle rating
    rating = None
    if rating_val:
        try:
            rating = int(rating_val)
            if 1 <= rating <= 5:
                VideoRating.objects.update_or_create(
                    video=video, user=request.user,
                    defaults={'rating': rating}
                )
            else:
                rating = None
        except ValueError:
            rating = None

    new_comment = Comment.objects.create(
        video=video,
        user=request.user,
        text=comment_text,
        rating=rating
    )
    
    # --- PERBAIKAN: Ambil info profil dengan aman ---
    profile_pic_url = ""
    user_initial = ""
    
    try:
        # Coba ambil profile. request.user dijamin ada karena @login_required
        profile = request.user.profile
        if profile and profile.foto_profil:
            profile_pic_url = profile.foto_profil # Model Anda pakai URLField
    except UserProfile.DoesNotExist:
        # Jika user (spt admin) tidak punya profil, biarkan saja
        pass 
    except AttributeError:
        # Penjagaan jika 'profile' tidak ada di request.user
        pass

    # Tentukan inisial JIKA tidak ada foto profil
    if not profile_pic_url:
        user_name = request.user.first_name or request.user.username
        user_initial = user_name[0].upper() if user_name else '?'
    # --- AKHIR PERBAIKAN ---

    # Kirim kembali data komentar yang baru dibuat
    return JsonResponse({
        'success': True,
        'comment': {
            'id': new_comment.id,
            'user': new_comment.user.username,
            'user_profile_pic': profile_pic_url, # <-- Aman
            'user_initial': user_initial,     # <-- Aman
            'text': new_comment.text,
            'rating': new_comment.rating,
            'helpful_count': new_comment.helpful_count,
            'created_at': timezone.localtime(new_comment.created_at).strftime("%d %b %Y, %H:%M")
        }
    })

@require_POST
def helpful_comment(request, comment_id):
    """Menambah 'helpful' ke komentar di DATABASE"""
    try:
        comment = get_object_or_404(Comment, pk=comment_id)
        
        # Cek jika user sudah menandai ini (opsional, via session)
        session_key = f'helpful_comment_{comment.id}'
        if request.session.get(session_key, False):
            return JsonResponse({'success': False, 'error': 'Already marked'}, status=400)

        comment.helpful_count = F('helpful_count') + 1
        comment.save(update_fields=['helpful_count'])
        comment.refresh_from_db()
        
        request.session[session_key] = True # Tandai di session
        
        return JsonResponse({
            'success': True, 
            'helpful_count': comment.helpful_count
        })
    except Comment.DoesNotExist:
         return JsonResponse({'success': False, 'error': 'Comment not found'}, status=404)