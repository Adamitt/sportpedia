import json
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.http import JsonResponse, Http404
from django.db.models import F, Q, Avg, Count # <-- Import Avg, Count
from django.views.decorators.http import require_POST
from django.utils import timezone # Untuk rating/comment

from .models import Video, Comment, VideoBookmark, VideoRating, VideoLike # <-- Import semua model
from .forms import VideoForm # Asumsi Anda punya ini
from sportlibrary.models import Sport
from metrics.utils import bump_view
from profile_app.models import UserProfile

from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, F
from django.shortcuts import get_object_or_404
from .models import Video, Comment, VideoRating

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
    try:
        # Query dengan annotate untuk rating dan likes
        videos_qs = Video.objects.select_related('sport', 'uploader').annotate(
            avg_rating=Avg('ratings__rating'),
            like_count=Count('likes', distinct=True)
        )
        
        sports = Sport.objects.all().order_by('name')
        
        # Search
        search_query = request.GET.get('search', '').strip()
        if search_query:
            videos_qs = videos_qs.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(instructor__icontains=search_query) |
                Q(tags__icontains=search_query)
            )

        # Filter by sport
        sport_filter = request.GET.get('sport')
        if sport_filter:
            try:
                videos_qs = videos_qs.filter(sport__id=int(sport_filter))
            except (ValueError, TypeError):
                pass  # Ignore invalid sport filter
        
        # Filter by difficulty
        difficulty_filter = request.GET.get('difficulty')
        if difficulty_filter:
            videos_qs = videos_qs.filter(difficulty=difficulty_filter)
        
        # Sorting
        sort_by = request.GET.get('sort', 'popular')
        if sort_by == 'rating':
            videos_qs = videos_qs.order_by('-avg_rating', '-views_count') 
        elif sort_by == 'newest':
            videos_qs = videos_qs.order_by('-created_at', '-views_count')
        elif sort_by == 'shortest':
            videos_qs = videos_qs.order_by('duration', '-views_count')
        else: # popular (default)
            videos_qs = videos_qs.order_by('-views_count', '-created_at')
        
        # Evaluate queryset menjadi list untuk template
        videos_list = list(videos_qs)
        
        # Auto-generate thumbnail dari YouTube URL jika thumbnail_url kosong
        import re
        for video in videos_list:
            if not video.thumbnail_url and video.video_url:
                # Extract YouTube video ID
                youtube_pattern = r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})'
                match = re.search(youtube_pattern, video.video_url)
                if match:
                    video_id = match.group(1)
                    video.thumbnail_url = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
                    # Save ke database untuk next time
                    Video.objects.filter(id=video.id).update(thumbnail_url=video.thumbnail_url)
        
        context = {
            'videos': videos_list,
            'sports': sports,
            'search_query': search_query,
            'selected_sport': sport_filter,
            'selected_difficulty': difficulty_filter,
            'sort_by': sort_by,
        }
        return render(request, 'videos/video_gallery.html', context)
    except Exception as e:
        # Log error untuk debugging
        import traceback
        print(f"Error di video_gallery: {e}")
        print(traceback.format_exc())
        # Return empty context dengan error message
        context = {
            'videos': [],
            'sports': Sport.objects.all().order_by('name'),
            'error_message': f'Error loading videos: {str(e)}',
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
@csrf_exempt
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

# ============================================
# API LOGIN ENDPOINT
# ============================================

@csrf_exempt
@require_POST
def api_login(request):
    """API endpoint untuk login."""
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return JsonResponse({
                'message': 'Username dan password harus diisi'
            }, status=400)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return JsonResponse({
                'message': 'Login berhasil',
                'username': user.username,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            }, status=200)
        else:
            return JsonResponse({
                'message': 'Username atau password salah'
            }, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'message': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


# ============================================
# VIDEO API ENDPOINTS
# ============================================

# Mapping difficulty dari model ke Flutter
DIFFICULTY_MAPPING = {
    'beginner': 'Pemula',
    'intermediate': 'Menengah',
    'advanced': 'Lanjutan',
}

# Mapping sebaliknya (dari Flutter ke model)
DIFFICULTY_REVERSE = {
    'Pemula': 'beginner',
    'Menengah': 'intermediate',
    'Lanjutan': 'advanced',
}

@require_GET
def api_video_list(request):
    """GET /videos/api/ - List semua video dengan filter optional"""
    videos_qs = Video.objects.select_related('sport', 'uploader').annotate(
        avg_rating=Avg('ratings__rating'),
        like_count=Count('likes')
    )
    
    # Search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        videos_qs = videos_qs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(instructor__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Filter by sport
    sport_id = request.GET.get('sport')
    if sport_id:
        try:
            sport_id = int(sport_id)
            videos_qs = videos_qs.filter(sport__id=sport_id)
        except ValueError:
            pass
    
    # Filter by difficulty (convert dari Flutter ke model format)
    difficulty = request.GET.get('difficulty')
    if difficulty:
        # Convert 'Pemula' -> 'beginner', dll
        difficulty_key = DIFFICULTY_REVERSE.get(difficulty, difficulty)
        videos_qs = videos_qs.filter(difficulty=difficulty_key)
    
    # Sorting
    sort_by = request.GET.get('sort', 'popular')
    if sort_by == 'rating':
        videos_qs = videos_qs.order_by('-avg_rating', '-views_count')
    elif sort_by == 'newest':
        videos_qs = videos_qs.order_by('-created_at', '-views_count')
    elif sort_by == 'views':
        videos_qs = videos_qs.order_by('-views_count', '-created_at')
    elif sort_by == 'shortest':
        videos_qs = videos_qs.order_by('duration', '-views_count')
    else:  # popular (default)
        videos_qs = videos_qs.order_by('-views_count', '-created_at')
    
    # Convert ke format JSON sesuai Flutter
    videos_data = []
    for video in videos_qs:
        # Convert difficulty dari model ke Flutter format
        difficulty_display = DIFFICULTY_MAPPING.get(video.difficulty, video.difficulty)
        
        videos_data.append({
            'id': video.id,
            'title': video.title,
            'description': video.description or '',
            'thumbnail': video.thumbnail_url or '',
            'url': video.video_url or '',
            'difficulty': difficulty_display,
            'sport_name': video.sport.name if video.sport else '',
            'duration': video.duration or '',
            'rating': float(video.avg_rating) if video.avg_rating else 0.0,
            'views': video.views_count or 0,
            'instructor': video.instructor or '',
            'tags': video.tags or [],
        })
    
    return JsonResponse(videos_data, safe=False)


@require_GET
def api_video_detail(request, video_id):
    """GET /videos/api/{id}/ - Detail satu video"""
    try:
        video = Video.objects.select_related('sport', 'uploader').annotate(
            avg_rating=Avg('ratings__rating'),
            like_count=Count('likes')
        ).get(pk=video_id)
    except Video.DoesNotExist:
        return JsonResponse({
            'error': 'Video tidak ditemukan'
        }, status=404)
    
    # Convert difficulty dari model ke Flutter format
    difficulty_display = DIFFICULTY_MAPPING.get(video.difficulty, video.difficulty)
    
    # Convert ke format JSON sesuai Flutter
    video_data = {
        'id': video.id,
        'title': video.title,
        'description': video.description or '',
        'thumbnail': video.thumbnail_url or '',
        'url': video.video_url or '',
        'difficulty': difficulty_display,
        'sport_name': video.sport.name if video.sport else '',
        'duration': video.duration or '',
        'rating': float(video.avg_rating) if video.avg_rating else 0.0,
        'views': video.views_count or 0,
    }
    
    return JsonResponse(video_data)


@require_GET
def api_video_comments(request, video_id):
    """GET /videos/api/{id}/comments/ - List komentar video dengan replies"""
    try:
        video = get_object_or_404(Video, pk=video_id)
    except Video.DoesNotExist:
        return JsonResponse({
            'error': 'Video tidak ditemukan'
        }, status=404)
    
    # Hanya ambil top-level comments (yang tidak punya parent)
    top_comments = Comment.objects.filter(
        video=video,
        parent__isnull=True
    ).select_related('user').prefetch_related('replies__user').order_by('-created_at')
    
    def serialize_comment(comment):
        """Helper function untuk serialize comment dengan replies"""
        replies_data = []
        for reply in comment.replies.all().order_by('created_at'):
            replies_data.append({
                'id': reply.id,
                'user': reply.user.username if reply.user else 'Anonymous',
                'text': reply.text,
                'rating': reply.rating,
                'helpful_count': reply.helpful_count or 0,
                'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M:%S') if reply.created_at else '',
                'parent_id': reply.parent.id if reply.parent else None,
            })
        
        return {
            'id': comment.id,
            'user': comment.user.username if comment.user else 'Anonymous',
            'text': comment.text,
            'rating': comment.rating,
            'helpful_count': comment.helpful_count or 0,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S') if comment.created_at else '',
            'replies': replies_data,
        }
    
    # Convert ke format JSON sesuai Flutter
    comments_data = [serialize_comment(comment) for comment in top_comments]
    
    return JsonResponse(comments_data, safe=False)


@csrf_exempt
@require_POST
def api_video_add_comment(request, video_id):
    """POST /videos/api/{id}/comment/ - Tambah komentar"""
    # Debug: print user info
    print(f"[DEBUG] api_video_add_comment - User: {request.user}, Authenticated: {request.user.is_authenticated}")
    print(f"[DEBUG] Session key: {request.session.session_key}")
    print(f"[DEBUG] Cookies: {request.COOKIES}")
    print(f"[DEBUG] Headers: {dict(request.headers)}")
    print(f"[DEBUG] Method: {request.method}")
    print(f"[DEBUG] Body: {request.body}")
    
    if not request.user.is_authenticated:
        print(f"[DEBUG] User NOT authenticated - returning 401")
        return JsonResponse({
            'error': 'Anda harus login terlebih dahulu',
            'debug': {
                'user': str(request.user),
                'is_authenticated': request.user.is_authenticated,
                'session_key': request.session.session_key,
                'cookies': dict(request.COOKIES),
            }
        }, status=401)
    
    print(f"[DEBUG] User authenticated - proceeding with comment creation")
    
    try:
        video = get_object_or_404(Video, pk=video_id)
    except Video.DoesNotExist:
        return JsonResponse({
            'error': 'Video tidak ditemukan'
        }, status=404)
    
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        rating = data.get('rating')
        
        if not text:
            return JsonResponse({
                'error': 'Text komentar harus diisi'
            }, status=400)
        
        # Handle rating jika ada
        if rating:
            try:
                rating = int(rating)
                if 1 <= rating <= 5:
                    VideoRating.objects.update_or_create(
                        video=video,
                        user=request.user,
                        defaults={'rating': rating}
                    )
                else:
                    rating = None
            except ValueError:
                rating = None
        
        # Buat komentar
        new_comment = Comment.objects.create(
            video=video,
            user=request.user,
            text=text,
            rating=rating
        )
        
        # Return dalam format JSON sesuai Flutter
        return JsonResponse({
            'id': new_comment.id,
            'user': new_comment.user.username,
            'text': new_comment.text,
            'rating': new_comment.rating,
            'helpful_count': new_comment.helpful_count or 0,
            'created_at': new_comment.created_at.strftime('%Y-%m-%d %H:%M:%S') if new_comment.created_at else '',
            'replies': [],  # New comment has no replies yet
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Gagal menambah komentar: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
def api_comment_reply(request, comment_id):
    """POST /videos/api/comment/{comment_id}/reply/ - Reply to a comment"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Anda harus login terlebih dahulu'
        }, status=401)
    
    try:
        parent_comment = get_object_or_404(Comment, pk=comment_id)
    except Comment.DoesNotExist:
        return JsonResponse({
            'error': 'Komentar tidak ditemukan'
        }, status=404)
    
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        
        if not text:
            return JsonResponse({
                'error': 'Text reply harus diisi'
            }, status=400)
        
        # Buat reply (komentar dengan parent)
        new_reply = Comment.objects.create(
            video=parent_comment.video,
            user=request.user,
            text=text,
            parent=parent_comment,
            rating=None  # Replies don't have ratings
        )
        
        # Return dalam format JSON sesuai Flutter
        return JsonResponse({
            'id': new_reply.id,
            'user': new_reply.user.username,
            'text': new_reply.text,
            'rating': None,
            'helpful_count': new_reply.helpful_count or 0,
            'created_at': new_reply.created_at.strftime('%Y-%m-%d %H:%M:%S') if new_reply.created_at else '',
            'parent_id': parent_comment.id,
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Gagal menambah reply: {str(e)}'
        }, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
def api_video_rate(request, video_id):
    """POST /videos/api/{id}/rate/ - Rate video"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Anda harus login terlebih dahulu'
        }, status=401)
    
    try:
        video = get_object_or_404(Video, pk=video_id)
    except Video.DoesNotExist:
        return JsonResponse({
            'error': 'Video tidak ditemukan'
        }, status=404)
    
    try:
        data = json.loads(request.body)
        rating = data.get('rating')
        
        if rating is None or not (1 <= rating <= 5):
            return JsonResponse({
                'error': 'Rating harus antara 1-5'
            }, status=400)
        
        # Simpan rating
        VideoRating.objects.update_or_create(
            video=video,
            user=request.user,
            defaults={'rating': rating}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Rating berhasil disimpan'
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


# ============================================
# ADMIN API ENDPOINTS (CRUD)
# ============================================

@csrf_exempt
@require_POST
def api_video_create(request):
    """POST /videos/api/create/ - Create video (Admin only)"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Anda harus login terlebih dahulu'
        }, status=401)
    
    if not request.user.is_staff:
        return JsonResponse({
            'error': 'Hanya admin yang dapat membuat video'
        }, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['title', 'description', 'sport', 'difficulty', 'video_url']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'error': f'Field {field} harus diisi'
                }, status=400)
        
        # Get sport
        try:
            sport_id = int(data['sport'])
            sport = Sport.objects.get(id=sport_id)
        except (ValueError, Sport.DoesNotExist):
            return JsonResponse({
                'error': 'Sport tidak valid'
            }, status=400)
        
        # Convert difficulty from Flutter format to model format
        difficulty = data.get('difficulty', 'Pemula')
        difficulty_key = DIFFICULTY_REVERSE.get(difficulty, 'beginner')
        
        # Auto-generate thumbnail from YouTube URL if not provided
        thumbnail_url = data.get('thumbnail_url', '')
        video_url = data.get('video_url', '')
        if not thumbnail_url and video_url:
            youtube_pattern = r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
            match = re.search(youtube_pattern, video_url)
            if match:
                video_id = match.group(1)
                thumbnail_url = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
        
        # Create video
        video = Video.objects.create(
            title=data['title'],
            description=data.get('description', ''),
            sport=sport,
            difficulty=difficulty_key,
            video_url=video_url,
            thumbnail_url=thumbnail_url,
            instructor=data.get('instructor', ''),
            duration=data.get('duration', ''),
            tags=data.get('tags', []),
            uploader=request.user,
        )
        
        # Return in Flutter format
        difficulty_display = DIFFICULTY_MAPPING.get(video.difficulty, video.difficulty)
        return JsonResponse({
            'id': video.id,
            'title': video.title,
            'description': video.description or '',
            'thumbnail': video.thumbnail_url or '',
            'url': video.video_url or '',
            'difficulty': difficulty_display,
            'sport_name': video.sport.name if video.sport else '',
            'duration': video.duration or '',
            'rating': 0.0,
            'views': video.views_count,
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


@csrf_exempt
@require_POST
def api_video_update(request, video_id):
    """POST /videos/api/{id}/update/ - Update video (Admin only)"""
    # Debug logging
    print(f'[DEBUG] api_video_update - User: {request.user}, Authenticated: {request.user.is_authenticated}, Staff: {request.user.is_staff if request.user.is_authenticated else False}')
    print(f'[DEBUG] api_video_update - Session key: {request.session.session_key if hasattr(request, "session") else "No session"}')
    print(f'[DEBUG] api_video_update - Cookies: {dict(request.COOKIES)}')
    print(f'[DEBUG] api_video_update - Headers: {dict(request.headers)}')
    
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Anda harus login terlebih dahulu',
            'debug': {
                'user': str(request.user),
                'is_authenticated': request.user.is_authenticated,
                'session_key': request.session.session_key if hasattr(request, 'session') else None,
                'cookies': dict(request.COOKIES),
            }
        }, status=401)
    
    if not request.user.is_staff:
        return JsonResponse({
            'error': 'Hanya admin yang dapat mengupdate video'
        }, status=403)
    
    try:
        video = get_object_or_404(Video, pk=video_id)
        data = json.loads(request.body)
        
        # Update fields
        if 'title' in data:
            video.title = data['title']
        if 'description' in data:
            video.description = data.get('description', '')
        if 'sport' in data:
            try:
                sport_id = int(data['sport'])
                sport = Sport.objects.get(id=sport_id)
                video.sport = sport
            except (ValueError, Sport.DoesNotExist):
                return JsonResponse({
                    'error': 'Sport tidak valid'
                }, status=400)
        if 'difficulty' in data:
            difficulty = data['difficulty']
            difficulty_key = DIFFICULTY_REVERSE.get(difficulty, 'beginner')
            video.difficulty = difficulty_key
        if 'video_url' in data:
            video.video_url = data['video_url']
        if 'thumbnail_url' in data:
            video.thumbnail_url = data['thumbnail_url']
        if 'instructor' in data:
            video.instructor = data.get('instructor', '')
        if 'duration' in data:
            video.duration = data.get('duration', '')
        if 'tags' in data:
            video.tags = data.get('tags', [])
        
        # Auto-generate thumbnail if video_url changed and thumbnail_url is empty
        if 'video_url' in data and not video.thumbnail_url:
            youtube_pattern = r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
            match = re.search(youtube_pattern, video.video_url or '')
            if match:
                video_id = match.group(1)
                video.thumbnail_url = f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'
        
        video.save()
        
        # Return in Flutter format
        difficulty_display = DIFFICULTY_MAPPING.get(video.difficulty, video.difficulty)
        return JsonResponse({
            'id': video.id,
            'title': video.title,
            'description': video.description or '',
            'thumbnail': video.thumbnail_url or '',
            'url': video.video_url or '',
            'difficulty': difficulty_display,
            'sport_name': video.sport.name if video.sport else '',
            'duration': video.duration or '',
            'rating': video.average_rating,
            'views': video.views_count,
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)


@require_GET
def api_sports_list(request):
    """GET /videos/api/sports/ - Get list of all sports"""
    from sportlibrary.models import Sport
    
    sports = Sport.objects.all().order_by('name')
    sports_data = [
        {
            'id': sport.id,
            'name': sport.name,
        }
        for sport in sports
    ]
    
    return JsonResponse(sports_data, safe=False)


@csrf_exempt
@require_POST
def api_video_delete(request, video_id):
    """POST /videos/api/{id}/delete/ - Delete video (Admin only)"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Anda harus login terlebih dahulu'
        }, status=401)
    
    if not request.user.is_staff:
        return JsonResponse({
            'error': 'Hanya admin yang dapat menghapus video'
        }, status=403)
    
    try:
        video = get_object_or_404(Video, pk=video_id)
        video_title = video.title
        video.delete()
        
        return JsonResponse({
            'message': f'Video "{video_title}" berhasil dihapus'
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Terjadi kesalahan: {str(e)}'
        }, status=500)

