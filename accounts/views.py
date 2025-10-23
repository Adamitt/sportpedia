from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from profile_app.models import UserProfile
from .forms import RegisterForm, LoginForm
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent.parent
USERS_PATH = BASE_DIR / 'database' / 'users.json'

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            profile = UserProfile.objects.create(user=user)
            
            try:
                if USERS_PATH.exists():
                    with open(USERS_PATH, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    data = []
                data.append(profile.to_json())
                with open(USERS_PATH, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Gagal simpan ke users.json: {e}")

            messages.success(request, 'Akun berhasil dibuat! Silakan login.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})



def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('/') 
        else:
            messages.error(request, 'Username atau password salah.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')