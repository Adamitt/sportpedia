from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from profile_app.models import UserProfile
from .forms import RegisterForm, LoginForm
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent.parent
USERS_PATH = BASE_DIR / 'database' / 'users.json'

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
def flutter_login(request):
    if request.method != 'POST':
        return JsonResponse(
            {'status': False, 'message': 'Invalid method'},
            status=405
        )

    try:
        # Kalau pbp_django_auth kirim form-encoded,
        # request.POST yang dipakai; kalau JSON, pakai body:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        username = data.get('username', '')
        password = data.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({
                'status': True,
                'message': 'Login berhasil',
                'username': user.username,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            })
        else:
            return JsonResponse({
                'status': False,
                'message': 'Username atau password salah.',
            }, status=401)
    except Exception as e:
        return JsonResponse({
            'status': False,
            'message': f'Terjadi error pada server: {e}',
        }, status=500)

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
            return redirect('accounts:login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})



def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # --- START: Added Check ---
            # Check if the user is staff or superuser
            if user.is_staff or user.is_superuser:
                # Redirect them to the admin dashboard
                # Make sure 'admin_sportpedia:dashboard' is the correct URL name!
                messages.success(request, f'Selamat datang kembali, Admin {user.username}!')
                return redirect('admin_sportpedia:dashboard') 
            else:
                # Redirect regular users to the homepage
                messages.success(request, f'Selamat datang kembali, {user.username}!')
                return redirect('/') 
            # --- END: Added Check ---

        else:
            # Keep the error message generic for security
            messages.error(request, 'Username atau password salah.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    storage = messages.get_messages(request)
    storage.used = True
    return redirect('accounts:login')