from django.shortcuts import redirect, render
from sportforum.models import ForumPost, Reply, Tag
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.template.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from sportforum.forms import ReplyForm, ForumPostForm
from datetime import datetime
from django.utils import timezone
import uuid
from django.contrib import messages


# Tampilkan semua forum post
def show_forum(request):
    """Menampilkan halaman forum (data dimuat via AJAX dari database)"""
    # Get categories for filter
    categories = [
        {'name': label, 'slug': value}
        for value, label in ForumPost.SPORT_CHOICES
    ]
    
    categories.sort(key=lambda x: x['name'])
    
    context = {
        'categories': categories,
        'selected_sport': request.GET.get('sport', ''),
    }
    return render(request, "sportforum/forum_post.html", context)


#Detail satu forum post (termasuk balasan)
def post_detail(request, id):
    """Menampilkan satu post beserta balasan menggunakan AJAX"""
    # Handle POST request for adding replies
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('accounts:login'))
        
        try:
            post = ForumPost.objects.get(pk=id)
            form = ReplyForm(request.POST)
            if form.is_valid():
                Reply.objects.create(
                    post=post,
                    user=request.user,
                    comment=form.cleaned_data['comment']
                )
                messages.success(request, "Reply added successfully!")
                return HttpResponseRedirect(request.path)
        except ForumPost.DoesNotExist:
            messages.warning(request, "Post not found.")
            return HttpResponseRedirect(reverse('sportforum:show_forum'))
    
    # Validate post exists for GET requests
    if not ForumPost.objects.filter(pk=id).exists():
        messages.warning(request, "Post not found or has been deleted.")
        return HttpResponseRedirect(reverse('sportforum:show_forum'))
    
    # Render template with AJAX
    context = {
        'id': str(id),
    }
    return render(request, "sportforum/post_detail.html", context)

@csrf_exempt
@login_required
def add_post_ajax(request):
    """Create forum post via AJAX"""
    if request.method == 'POST':
        try:
            sport = request.POST.get('sport')
            title = request.POST.get('title')
            content = request.POST.get('content')
            tags_input = request.POST.get('tags', '')
            
            # Validate required fields
            if not sport or not title or not content:
                return JsonResponse({
                    'error': 'All fields are required'
                }, status=400)
            
            # Create new post
            new_post = ForumPost.objects.create(
                sport=sport,
                title=title,
                content=content,
                author=request.user
            )
            
            # Handle tags
            if tags_input:
                tags = [t.strip() for t in tags_input.split(',') if t.strip()]
                for tag_name in tags:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    new_post.tags.add(tag)
            
            return JsonResponse({
                'success': True,
                'message': 'Post created successfully',
                'post_id': str(new_post.id)
            }, status=201)
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'error': 'Invalid request method'
    }, status=405)


def toggle_like(request, id):
    """Toggle like untuk post - dengan pengecekan manual untuk AJAX"""
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('sportforum:post_detail', args=[id]))
    
    # Check authentication manually for better AJAX handling
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'You must be logged in to like posts',
                'authenticated': False
            }, status=403)
        else:
            return HttpResponseRedirect(reverse('accounts:login'))
    
    post = get_object_or_404(ForumPost, pk=id)
    
    # Toggle like
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    
    # Return JSON untuk AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'total_likes': post.total_likes,
            'authenticated': True
        })
    
    # Redirect untuk non-AJAX request
    return HttpResponseRedirect(reverse('sportforum:post_detail', args=[id]))

@login_required
def edit_post(request, id):
    """Edit forum post - hanya author yang bisa edit"""
    post = get_object_or_404(ForumPost, pk=id)
    
    # Check authorization - only author can edit
    if request.user != post.author:
        from django.contrib import messages
        messages.error(request, "You are not authorized to edit this post.")
        return HttpResponseRedirect(reverse('sportforum:post_detail', args=[id]))
    
    # Populate initial tags as comma-separated string
    initial_tags = ', '.join([tag.name for tag in post.tags.all()])
    
    if request.method == 'POST':
        form = ForumPostForm(request.POST, instance=post)
        if form.is_valid():
            updated_post = form.save()
            
            # Handle tags
            if form.cleaned_data.get('tags'):
                # Clear existing tags
                updated_post.tags.clear()
                
                # Add new tags
                tags = [t.strip() for t in form.cleaned_data['tags'].split(',') if t.strip()]
                for tag_name in tags:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    updated_post.tags.add(tag)
            else:
                # Clear all tags if field is empty
                updated_post.tags.clear()
            
            return HttpResponseRedirect(reverse('sportforum:post_detail', args=[id]))
    else:
        form = ForumPostForm(instance=post, initial={'tags': initial_tags})

    context = {
        'form': form,
        'post': post,
    }
    return render(request, "sportforum/edit_post.html", context)

@login_required
def delete_post(request, id):
    """Delete forum post - hanya author yang bisa delete"""
    post = get_object_or_404(ForumPost, pk=id)
    
    # Check authorization - only author can delete
    if request.user != post.author:
        messages.error(request, "You are not authorized to delete this post.")
        return HttpResponseRedirect(reverse('sportforum:post_detail', args=[id]))
    
    post.delete()
    return HttpResponseRedirect(reverse('sportforum:show_forum'))


def show_json(request):
    """Return all forum posts as JSON (from database only)"""
    sport_filter = request.GET.get('sport')
    
    # Get posts from database
    posts = ForumPost.objects.all()
    if sport_filter:
        posts = posts.filter(sport=sport_filter)
    
    data = []
    
    # Convert database posts to JSON
    for post in posts:
        data.append({
            'id': str(post.id),
            'sport': post.get_sport_display(),
            'sport_slug': post.sport,
            'title': post.title,
            'author': post.author.username,
            'content': post.content,
            'likes': post.total_likes,
            'views': post.views,
            'date_posted': post.date_posted.isoformat() if post.date_posted else None,
            'tags': [tag.name for tag in post.tags.all()],
            'replies_count': post.replies.count(),
            'source': 'database',
        })
    
    return JsonResponse(data, safe=False)


def show_json_by_id(request, id):
    """Return single forum post by ID as JSON"""
    try:
        post = ForumPost.objects.select_related('author').prefetch_related('tags', 'replies').get(pk=id)
        
        # Increment view count
        post.views += 1
        post.save(update_fields=['views'])
        
        # Get replies data
        replies_data = [
            {
                'user': reply.user.username,
                'comment': reply.comment,
                'date': reply.date.isoformat() if reply.date else None,
            }
            for reply in post.replies.all()
        ]
        
        # Check if current user has liked the post
        user_has_liked = False
        if request.user.is_authenticated:
            user_has_liked = post.likes.filter(id=request.user.id).exists()
        
        data = {
            'id': str(post.id),
            'sport': post.get_sport_display(),
            'sport_slug': post.sport,
            'title': post.title,
            'author': post.author.username,
            'content': post.content,
            'likes': post.total_likes,
            'views': post.views,
            'date_posted': post.date_posted.isoformat() if post.date_posted else None,
            'tags': [tag.name for tag in post.tags.all()],
            'replies': replies_data,
            'replies_count': len(replies_data),
            'user_has_liked': user_has_liked,
            'can_edit': request.user.is_authenticated and request.user == post.author,
            'source': 'database',
        }
        
        return JsonResponse(data)
    except ForumPost.DoesNotExist:
        return JsonResponse({'detail': 'Not found'}, status=404)

