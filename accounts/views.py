from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
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
            
            # Ensure session is created
            if not request.session.session_key:
                request.session.create()
            
            # Debug logging
            print(f"[DEBUG] flutter_login - User: {user.username}, Authenticated: {request.user.is_authenticated}")
            print(f"[DEBUG] flutter_login - Session key: {request.session.session_key}")
            print(f"[DEBUG] flutter_login - Cookies in request: {dict(request.COOKIES)}")
            
            return JsonResponse({
                'status': True,
                'message': 'Login berhasil',
                'username': user.username,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'session_key': request.session.session_key,  # Include session key for Flutter Web
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


# ============================================
# API ENDPOINTS untuk Flutter
# ============================================

@csrf_exempt
def api_login(request):
    """API login untuk Flutter (dari branch pudil-feature-login)
    
    Support both JSON (Flutter) dan form data (Postman).
    Menggunakan session Django yang sama dengan web app.
    """
    if request.method == 'POST':
        # Support both JSON dan form data
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                username = data.get('username', '').strip()
                password = data.get('password', '')
            except json.JSONDecodeError:
                return JsonResponse({
                    "status": False,
                    "message": "Invalid JSON format."
                }, status=400)
        else:
            # Form data (untuk kompatibilitas)
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
        
        if not username or not password:
            return JsonResponse({
                "status": False,
                "message": "Username dan password harus diisi."
            }, status=400)
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                # Login user (membuat session yang sama dengan web)
                login(request, user)
                # Pastikan UserProfile ada (dari implementasi Fadhil)
                profile, created = UserProfile.objects.get_or_create(user=user)
                
                # Debug: print session info
                print(f"[DEBUG] api_login - User: {user.username}, Authenticated: {request.user.is_authenticated}")
                print(f"[DEBUG] api_login - Session key: {request.session.session_key}")
                print(f"[DEBUG] api_login - Session cookie name: {settings.SESSION_COOKIE_NAME}")
                print(f"[DEBUG] api_login - Response headers will include Set-Cookie")
                
                # Ensure session cookie is set
                if not request.session.session_key:
                    request.session.create()
                    print(f"[DEBUG] api_login - Created new session: {request.session.session_key}")
                
                response = JsonResponse({
                    "username": user.username,
                    "status": True,
                    "message": "Login berhasil!",
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                    "session_key": request.session.session_key,  # Include session key in response for Flutter Web
                }, status=200)
                
                print(f"[DEBUG] api_login - Session key included in response: {request.session.session_key}")
                
                return response
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


@require_GET
def api_user_info(request):
    """GET /accounts/api/user-info/ - Get current user info"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'authenticated': False,
        }, status=401)
    
    return JsonResponse({
        'authenticated': True,
        'username': request.user.username,
        'is_staff': request.user.is_staff,
        'is_superuser': request.user.is_superuser,
    })


@require_POST
def api_logout(request):
    """API endpoint untuk logout dari Flutter mobile app."""
    if request.user.is_authenticated:
        logout(request)
        return JsonResponse({
            'message': 'Logout berhasil'
        }, status=200)
    else:
        return JsonResponse({
            'message': 'Anda belum login'
        }, status=401)