from django.shortcuts import render, get_object_or_404
from .forms import PostForm, CommentForm
from .models import Post, Group, User, Comment, Follow
from django.utils import timezone
from django.shortcuts import redirect
from django import forms
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page


def index(request):
        post_list = Post.objects.order_by("-pub_date").all()
        paginator = Paginator(post_list, 10) # показывать по 10 записей на странице.
        page_number = request.GET.get('page') # переменная в URL с номером запрошенной страницы
        page = paginator.get_page(page_number) # получить записи с нужным смещением
        form = PostForm(request.POST or None, files=request.FILES or None)
        return render(request, 'index.html', {'page': page, 'paginator': paginator, 'form': form})

def group_posts(request, slug): 
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group).order_by("-pub_date")[:12]
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"group": group, 'page': page, 'paginator': paginator}) 

@login_required
def new_post(request):
    title = 'Добавить запись'
    button = 'Добавить'
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post:index')
    form = PostForm(files=request.FILES or None)
    return render(request, 'new_post.html', {'form': form, 'title' : title, 'button' : button})
    
def profile(request, username):
        profile = get_object_or_404(User, username=username)
        post_list = Post.objects.filter(author=profile.pk).order_by("-pub_date")
        id_of_post = Post.objects.filter(author=profile.pk, id=None)
        posts_all = Post.objects.filter(author = profile).order_by('-pub_date').all()
        posts_count = posts_all.count()
        #follower_count = 
        paginator = Paginator(post_list, 10) # показывать по 10 записей на странице.
        page_number = request.GET.get('page') # переменная в URL с номером запрошенной страницы
        page = paginator.get_page(page_number) # получить записи с нужным смещением
        form = PostForm(request.POST or None, files=request.FILES or None)
        return render(request, "profile.html", {"profile":profile, 'post_list':post_list, 
        "count":posts_count, 'post_id':id_of_post,'page':page, "paginator": paginator, 'form': form})
        
        
def post_view(request, username, post_id):
        # тут тело функции
        profile = get_object_or_404(User, username=username)
        post = get_object_or_404(Post, author=profile.pk, id=post_id)
        count = Post.objects.filter(author = profile).count
        form = CommentForm()
        comments = Comment.objects.filter(post=post_id)
        return render(request, "post.html", {"profile":profile, 'post':post, "count":count, 'form': form, 'comments' : comments})


def post_edit(request, username, post_id):
    title = 'Редактировать запись'
    button = 'Сохранить'
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('post:post', username=username, post_id=post_id) 
    if request.method == "POST":
        form = PostForm(request.POST, files=request.FILES or None, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post:post', username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    return render(request, 'post_edit.html', {'form': form, 'title' : title, 'button' : button, 'post': post})


        
def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)
    
    
def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    #comments = Comment.objects.filter(post=post).order_by('-created').all()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            return redirect('post:post', username=username, post_id=post_id)
    form = CommentForm()
    return redirect('post:post', username=post.author.username, post_id=post_id)


@login_required
def follow_index(request):
    following = Follow.objects.filter(user=request.user).all()
    author_list = []
    for author in following:
        author_list.append(author.author.id)
    post_list = Post.objects.filter(author__in=author_list).order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {'page': page, 'paginator': paginator})



@login_required
def profile_follow(request, username):
    user = request.user.id
    author = User.objects.get(username=username)
    follow_check = Follow.objects.filter(user=user, author=author.id).count()
    if follow_check == 0 and request.user.username != username:
        Follow.objects.create(user=request.user, author=author)
    return redirect("post:profile", username=username)

@login_required
def profile_unfollow(request, username):
    user = request.user.id
    author = User.objects.get(username=username)
    follow_check = Follow.objects.filter(user=user, author=author.id).count()
    if follow_check == 1:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect("post:profile", username=username)


