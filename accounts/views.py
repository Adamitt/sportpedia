from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from profile_app.models import UserProfile

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, 'Password tidak cocok.')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username sudah digunakan.')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email sudah digunakan.')
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()
        UserProfile.objects.create(user=user)
        messages.success(request, 'Akun berhasil dibuat! Silakan login.')
        return redirect('login')

    return render(request, 'accounts/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('profile_page')
        else:
            messages.error(request, 'Username atau password salah')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')
