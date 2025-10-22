from django.shortcuts import render
from sportforum.models import SportCategory, ForumPost, Reply, Tag
# Create your views here.
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.template.context_processors import csrf
from django.contrib.auth.decorators import login_required

from sportforum.models import SportCategory, ForumPost, Reply, Tag
from sportforum.forms import ReplyForm, ForumPostForm


# Daftar kategori olahraga
def index(request):
    """Menampilkan daftar kategori olahraga"""
    categories = SportCategory.objects.all().order_by('name')
    return render(request, "sportforum/category_list.html", {'categories': categories})


# Daftar forum dalam satu kategori
def category_detail(request, category_slug):
    """Menampilkan semua post dalam kategori tertentu"""
    category = get_object_or_404(SportCategory, name__iexact=category_slug)
    posts = ForumPost.objects.filter(sport=category).order_by('-date_posted')
    return render(request, "sportforum/forum_list.html", {'category': category, 'posts': posts})


#Detail satu forum post (termasuk balasan)
def post_detail(request, slug):
    """Menampilkan satu post beserta balasan"""
    post = get_object_or_404(ForumPost, slug=slug)
    post.views += 1
    post.save()

    replies = Reply.objects.filter(post=post).order_by('date')
    form = ReplyForm()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('login'))
        form = ReplyForm(request.POST)
        if form.is_valid():
            Reply.objects.create(
                post=post,
                user=request.user,
                comment=form.cleaned_data['comment']
            )
            return HttpResponseRedirect(reverse('post_detail', args=[post.slug]))

    return render(request, "sportforum/post_detail.html", {
        'post': post,
        'replies': replies,
        'form': form
    })


# Membuat post baru dalam kategori tertentu
@login_required
def new_post(request, category_slug):
    """Membuat forum post baru di kategori olahraga tertentu"""
    category = get_object_or_404(SportCategory, name__iexact=category_slug)
    form = ForumPostForm()

    if request.method == 'POST':
        form = ForumPostForm(request.POST)
        if form.is_valid():
            new_post = ForumPost.objects.create(
                sport=category,
                title=form.cleaned_data['title'],
                content=form.cleaned_data['content'],
                author=request.user
            )
            if form.cleaned_data.get('tags'):
                tags = [t.strip() for t in form.cleaned_data['tags'].split(',')]
                for tag_name in tags:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    new_post.tags.add(tag)

            return HttpResponseRedirect(reverse('post_detail', args=[new_post.slug]))

    return render(request, "sportforum/new_post.html", {'form': form, 'category': category})

@login_required
def toggle_like(request, slug):
    """Menambah atau menghapus like pada post"""
    post = get_object_or_404(ForumPost, slug=slug)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return HttpResponseRedirect(reverse('post_detail', args=[slug]))
