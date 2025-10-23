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
    """Menampilkan semua forum post dengan filter kategori opsional (dari DB + JSON)"""
    # Filter berdasarkan kategori jika ada query parameter
    sport_filter = request.GET.get('sport')
    
    # Ambil data dari database SQL
    sql_posts = ForumPost.objects.all()
    if sport_filter:
        sql_posts = sql_posts.filter(sport=sport_filter)
    
    posts_list = []
    
    # Convert database posts ke format dict
    for post in sql_posts:
        posts_list.append({
            'id': str(post.id),
            'sport': post.get_sport_display(),
            'sport_slug': post.sport,
            'title': post.title,
            'author': post.author.username,
            'content': post.content,
            'likes': post.total_likes,
            'views': post.views,
            'date_posted': post.date_posted,
            'tags': [tag.name for tag in post.tags.all()],
            'replies_count': post.replies.count(),
            'source': 'database',
            'post_object': post,  \
        })
    
    # Ambil data dari JSON
    json_posts = load_forum_json()
    for json_post in json_posts:
        # Filter berdasarkan sport jika ada
        if sport_filter:
            sport_slug = json_post.get('sport', '').lower().replace(' ', '-')
            if sport_slug != sport_filter:
                continue
        
        posts_list.append({
            'id': f"json_{json_post['id']}",
            'sport': json_post.get('sport', ''),
            'sport_slug': json_post.get('sport', '').lower().replace(' ', '-'),
            'title': json_post.get('title', ''),
            'author': json_post.get('author', 'Anonymous'),
            'content': json_post.get('content', ''),
            'likes': json_post.get('likes', 0),
            'views': json_post.get('views', 0),
            'date_posted': datetime.strptime(json_post.get('date_posted', '2025-01-01'), '%Y-%m-%d'),
            'tags': json_post.get('tags', []),
            'replies_count': len(json_post.get('replies', [])),
            'source': 'json',
        })
    
    # Sort by date_posted (newest first)
    posts_list.sort(key=lambda x: x['date_posted'], reverse=True)
    
    # Implementasi Pagination (6 posts per halaman)
    paginator = Paginator(posts_list, 6)  # 6 posts per page
    page_number = request.GET.get('page', 1)
    
    try:
        posts_page = paginator.get_page(page_number)
    except PageNotAnInteger:
        posts_page = paginator.get_page(1)
    except EmptyPage:
        posts_page = paginator.get_page(paginator.num_pages)
    
    categories = [
        {'name': label, 'slug': value}
        for value, label in ForumPost.SPORT_CHOICES
    ]
    
    existing_slugs = {cat['slug'] for cat in categories}
    json_sports = set()
    for json_post in json_posts:
        sport_name = json_post.get('sport', '')
        if sport_name:
            sport_slug = sport_name.lower().replace(' ', '-')
            if sport_slug not in existing_slugs:
                json_sports.add((sport_slug, sport_name))
    
    # Add JSON sports to categories
    for slug, name in json_sports:
        categories.append({
            'name': name,
            'slug': slug,
            'source': 'json'
        })
    
    # Sort berdasarkan nama
    categories.sort(key=lambda x: x['name'])
    
    context = {
        'posts': posts_page, 
        'categories': categories,  
        'selected_sport': sport_filter,
        'paginator': paginator,
    }
    return render(request, "sportforum/forum_post.html", context)


#Detail satu forum post (termasuk balasan)
def post_detail(request, id):
    """Menampilkan satu post beserta balasan (dari DB atau JSON)"""
    post_data = None
    
    # Check if id is from JSON:
    # Has prefix "json_" OR
    # Is a simple integer (not UUID format)
    is_json_post = False
    json_id = None
    
    if str(id).startswith('json_'):
        is_json_post = True
        json_id = int(str(id).replace('json_', ''))
    else:
        # Try to convert to int - if success, it's from JSON
        try:
            json_id = int(id)
            is_json_post = True
        except (ValueError, TypeError):
            is_json_post = False
    
    if is_json_post:
        json_posts = load_forum_json()
        
        for post in json_posts:
            if post['id'] == json_id:
                post_data = {
                    'id': f"json_{post['id']}",
                    'sport': post.get('sport', ''),
                    'title': post.get('title', ''),
                    'author': post.get('author', 'Anonymous'),
                    'content': post.get('content', ''),
                    'likes': post.get('likes', 0),
                    'views': post.get('views', 0),
                    'date_posted': datetime.strptime(post.get('date_posted', '2025-01-01'), '%Y-%m-%d'),
                    'tags': post.get('tags', []),
                    'replies': [
                        {
                            'user': reply.get('user', 'Anonymous'),
                            'comment': reply.get('comment', ''),
                            'date': datetime.strptime(reply.get('date', '2025-01-01'), '%Y-%m-%d')
                        }
                        for reply in post.get('replies', [])
                    ],
                    'source': 'json',
                    'is_readonly': True
                }
                break
    else:
        try:
            post = ForumPost.objects.get(pk=id)
            post.views += 1
            post.save()
            
            replies = Reply.objects.filter(post=post).order_by('date')
            
            post_data = {
                'id': str(post.id),
                'sport': post.get_sport_display(),
                'title': post.title,
                'author': post.author.username,
                'content': post.content,
                'likes': post.total_likes,
                'views': post.views,
                'date_posted': post.date_posted,
                'tags': [tag.name for tag in post.tags.all()],
                'replies': [
                    {
                        'user': reply.user.username,
                        'comment': reply.comment,
                        'date': reply.date
                    }
                    for reply in replies
                ],
                'source': 'database',
                'is_readonly': False,
                'post_object': post
            }
        except ForumPost.DoesNotExist:
            pass
    
    if not post_data:
        raise Http404("Post not found")
    
    form = ReplyForm()

    # Handle POST request (hanya untuk database posts)
    if request.method == 'POST':
        if post_data['source'] == 'json':
            from django.contrib import messages
            messages.warning(request, "Cannot add reply to archived posts from JSON.")
            return HttpResponseRedirect(reverse('sportforum:post_detail', args=[id]))
        
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('main:login'))
        
        form = ReplyForm(request.POST)
        if form.is_valid() and 'post_object' in post_data:
            Reply.objects.create(
                post=post_data['post_object'],
                user=request.user,
                comment=form.cleaned_data['comment']
            )
            return HttpResponseRedirect(reverse('sportforum:post_detail', args=[id]))
    
    context = {
        'post': post_data,
        'replies': post_data.get('replies', []),
        'form': form,
        'is_readonly': post_data.get('is_readonly', False)
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

@login_required
def toggle_like(request, id):
    if request.method != 'POST':
        return HttpResponseRedirect(reverse('post_detail', args=[id]))
    
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
            'total_likes': post.total_likes
        })
    
    # Redirect untuk non-AJAX request
    return HttpResponseRedirect(reverse('post_detail', args=[id]))

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
