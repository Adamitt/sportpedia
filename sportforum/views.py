from django.shortcuts import redirect, render
from sportforum.models import ForumPost, Reply, Tag
# Create your views here.
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.template.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from sportforum.models import ForumPost, Reply, Tag
from sportforum.forms import ReplyForm, ForumPostForm
from datetime import datetime
from django.utils import timezone
from pathlib import Path
import uuid
import json
from django.contrib import messages


def load_forum_json():
    """Load forum posts dari JSON file"""
    base_dir = Path(__file__).resolve().parent.parent
    data_path = base_dir / 'database' / 'forum.json'
    
    try:
        with open(data_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# Tampilkan semua forum post
def show_forum(request):
    """Menampilkan halaman forum (data dimuat via AJAX)"""
    # Get categories for filter
    categories = [
        {'name': label, 'slug': value}
        for value, label in ForumPost.SPORT_CHOICES
    ]
    
    # Add JSON sports to categories
    json_posts = load_forum_json()
    existing_slugs = {cat['slug'] for cat in categories}
    json_sports = set()
    for json_post in json_posts:
        sport_name = json_post.get('sport', '')
        if sport_name:
            sport_slug = sport_name.lower().replace(' ', '-')
            if sport_slug not in existing_slugs:
                json_sports.add((sport_slug, sport_name))
    
    for slug, name in json_sports:
        categories.append({
            'name': name,
            'slug': slug,
            'source': 'json'
        })
    
    categories.sort(key=lambda x: x['name'])
    
    context = {
        'categories': categories,
        'selected_sport': request.GET.get('sport', ''),
    }
    return render(request, "sportforum/forum_post.html", context)


#Detail satu forum post (termasuk balasan)
def post_detail(request, id):
    """Menampilkan satu post beserta balasan menggunakan AJAX"""
    # Handle POST request for adding replies (for database posts only) FIRST
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('accounts:login'))
        
        # Only allow replies on database posts (not JSON posts)
        if str(id).startswith('json_'):
            messages.warning(request, "Cannot reply to this post.")
            return HttpResponseRedirect(request.path)
        
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
                # Redirect back to same post using the post's actual ID
                return HttpResponseRedirect(request.path)
        except ForumPost.DoesNotExist:
            messages.warning(request, "Post not found.")
            return HttpResponseRedirect(reverse('sportforum:show_forum'))
    
    # Validate post exists (database or JSON) for GET requests
    post_exists = False
    
    # Check if it's a JSON post
    if str(id).startswith('json_'):
        json_posts = load_forum_json()
        json_id = str(id).replace('json_', '')
        try:
            json_id_int = int(json_id)
            json_post = next((p for p in json_posts if p['id'] == json_id_int), None)
            if json_post:
                post_exists = True
        except (ValueError, StopIteration):
            pass
    else:
        # Check if it's a database post
        post_exists = ForumPost.objects.filter(pk=id).exists()
    
    # If post doesn't exist, redirect to forum list
    if not post_exists:
        messages.warning(request, "Post not found or has been deleted.")
        return HttpResponseRedirect(reverse('sportforum:show_forum'))
    
    # For GET request, just render the template with AJAX
    context = {
        'id': id,
    }
    return render(request, "sportforum/post_detail.html", context)


# Membuat post baru
@login_required
def new_post(request):
    """Membuat forum post baru"""
    form = ForumPostForm()

    if request.method == 'POST':
        form = ForumPostForm(request.POST)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            
            # Handle tags
            if form.cleaned_data.get('tags'):
                tags = [t.strip() for t in form.cleaned_data['tags'].split(',') if t.strip()]
                for tag_name in tags:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    new_post.tags.add(tag)

            return HttpResponseRedirect(reverse('sportforum:post_detail', args=[new_post.id]))

    context = {
        'form': form,
    }
    return render(request, "sportforum/new_post.html", context)

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
    """Return all forum posts as JSON (from database + JSON files)"""
    sport_filter = request.GET.get('sport')
    
    # Get SQL posts
    sql_posts = ForumPost.objects.all()
    if sport_filter:
        sql_posts = sql_posts.filter(sport=sport_filter)
    
    data = []
    
    # Convert database posts
    for post in sql_posts:
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
    
    # Get JSON posts
    json_posts = load_forum_json()
    for json_post in json_posts:
        # Filter by sport if needed
        if sport_filter:
            sport_slug = json_post.get('sport', '').lower().replace(' ', '-')
            if sport_slug != sport_filter:
                continue
        
        data.append({
            'id': f"json_{json_post['id']}",
            'sport': json_post.get('sport', ''),
            'sport_slug': json_post.get('sport', '').lower().replace(' ', '-'),
            'title': json_post.get('title', ''),
            'author': json_post.get('author', 'Anonymous'),
            'content': json_post.get('content', ''),
            'likes': json_post.get('likes', 0),
            'views': json_post.get('views', 0),
            'date_posted': json_post.get('date_posted', '2025-01-01'),
            'tags': json_post.get('tags', []),
            'replies_count': len(json_post.get('replies', [])),
            'source': 'json',
        })
    
    # Sort by date (newest first)
    data.sort(key=lambda x: x['date_posted'], reverse=True)
    
    return JsonResponse(data, safe=False)


def show_json_by_id(request, id):
    """Return single forum post by ID as JSON"""
    # Check if it's a JSON file post (ID starts with 'json_')
    if str(id).startswith('json_'):
        json_posts = load_forum_json()
        json_id = str(id).replace('json_', '')
        
        try:
            json_id_int = int(json_id)
            json_post = next((p for p in json_posts if p['id'] == json_id_int), None)
            
            if json_post:
                data = {
                    'id': f"json_{json_post['id']}",
                    'sport': json_post.get('sport', ''),
                    'sport_slug': json_post.get('sport', '').lower().replace(' ', '-'),
                    'title': json_post.get('title', ''),
                    'author': json_post.get('author', 'Anonymous'),
                    'content': json_post.get('content', ''),
                    'likes': json_post.get('likes', 0),
                    'views': json_post.get('views', 0),
                    'date_posted': json_post.get('date_posted', '2025-01-01'),
                    'tags': json_post.get('tags', []),
                    'replies': json_post.get('replies', []),
                    'replies_count': len(json_post.get('replies', [])),
                    'user_has_liked': False,  # JSON posts can't be liked
                    'can_edit': False,  # JSON posts can't be edited
                    'source': 'json',
                }
                return JsonResponse(data)
        except (ValueError, StopIteration):
            pass
        
        return JsonResponse({'detail': 'Not found'}, status=404)
    
    # Handle database posts
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

