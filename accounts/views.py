from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from profile_app.models import UserProfile
from .forms import RegisterForm, LoginForm
from pathlib import Path
import json


BASE_DIR = Path(__file__).resolve().parent.parent.parent
USERS_PATH = BASE_DIR / 'database' / 'users.json'


# ===================== API Views untuk Flutter =====================

@csrf_exempt
def api_login(request):
    """API login untuk Flutter"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                auth_login(request, user)
                profile, created = UserProfile.objects.get_or_create(user=user)
                return JsonResponse({
                    "username": user.username,
                    "status": True,
                    "message": "Login berhasil!",
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                }, status=200)
            else:
                return JsonResponse({
                    "status": False,
                    "message": "Login gagal, akun dinonaktifkan."
                }, status=401)
        else:
            return JsonResponse({
                "status": False,
                "message": "Login gagal, periksa username atau password."
            }, status=401)
    
    return JsonResponse({
        "status": False,
        "message": "Invalid request method."
    }, status=400)


@csrf_exempt
def api_register(request):
    """API register untuk Flutter"""
    if request.method == 'POST':
        try:
            # Support both JSON and form data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                username = data.get('username')
                password1 = data.get('password1')
                password2 = data.get('password2')
                email = data.get('email', '')
            else:
                # Form data (dari pbp_django_auth post())
                username = request.POST.get('username')
                password1 = request.POST.get('password1')
                password2 = request.POST.get('password2')
                email = request.POST.get('email', '')

            if password1 != password2:
                return JsonResponse({
                    "status": False,
                    "message": "Password tidak cocok."
                }, status=400)

            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    "status": False,
                    "message": "Username sudah digunakan."
                }, status=400)

            if email and User.objects.filter(email=email).exists():
                return JsonResponse({
                    "status": False,
                    "message": "Email sudah digunakan."
                }, status=400)

            user = User.objects.create_user(username=username, password=password1, email=email)
            user.save()
            UserProfile.objects.create(user=user)

            return JsonResponse({
                "username": user.username,
                "status": "success",
                "message": "User berhasil dibuat!"
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({
                "status": False,
                "message": "Invalid JSON data."
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": str(e)
            }, status=500)

    return JsonResponse({
        "status": False,
        "message": "Invalid request method."
    }, status=400)


@csrf_exempt
def api_logout(request):
    """API logout untuk Flutter"""
    username = request.user.username
    try:
        auth_logout(request)
        return JsonResponse({
            "username": username,
            "status": True,
            "message": "Logout berhasil!"
        }, status=200)
    except Exception as e:
        return JsonResponse({
            "status": False,
            "message": f"Logout gagal: {str(e)}"
        }, status=401)


@csrf_exempt
def api_user_info(request):
    """API untuk mendapatkan info user yang sedang login"""
    if request.user.is_authenticated:
        return JsonResponse({
            "status": True,
            "username": request.user.username,
            "email": request.user.email,
            "is_staff": request.user.is_staff,
            "is_superuser": request.user.is_superuser,
        }, status=200)
    else:
        return JsonResponse({
            "status": False,
            "message": "User not authenticated"
        }, status=401)


# ===================== Web Views (HTML) =====================

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

            messages.success(request, '🎉 Akun berhasil dibuat! Silakan login.')
            return redirect('accounts:login')
        else:
            # Tampilkan error dari form sebagai toast
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f'❌ {error}')
                    else:
                        field_label = form.fields[field].label or field.replace('_', ' ').title()
                        messages.error(request, f'❌ {field_label}: {error}')
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
    username = request.user.username if request.user.is_authenticated else ''
    logout(request)
    messages.success(request, f'👋 Sampai jumpa lagi, {username}! Anda telah berhasil logout.')
    return redirect('accounts:login')