from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from profile_app.models import UserProfile
from .forms import RegisterForm, LoginForm
import json

# ===================== API Views untuk Flutter =====================

@csrf_exempt
def api_login(request):
    """
    API login untuk Flutter.
    Menerima username & password, mengembalikan status login & role user.
    """
    if request.method == 'POST':
        # Coba ambil dari POST data (Form-data) atau JSON Body
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Jika tidak ada di POST, coba ambil dari raw JSON body
        if not username:
            try:
                data = json.loads(request.body.decode('utf-8'))
                username = data.get('username')
                password = data.get('password')
            except Exception:
                pass

        # Autentikasi user
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                auth_login(request, user)
                
                # Pastikan UserProfile ada (buat baru jika belum ada)
                UserProfile.objects.get_or_create(user=user)
                
                return JsonResponse({
                    "status": True,
                    "message": "Login berhasil!",
                    "username": user.username,
                    "is_staff": user.is_staff,       # Penting untuk logika Admin di Flutter
                    "is_superuser": user.is_superuser # Penting untuk logika Admin di Flutter
                }, status=200)
            else:
                return JsonResponse({
                    "status": False,
                    "message": "Login gagal, akun dinonaktifkan."
                }, status=401)
        else:
            return JsonResponse({
                "status": False,
                "message": "Username atau password salah."
            }, status=401)
    
    return JsonResponse({
        "status": False,
        "message": "Invalid request method."
    }, status=400)


@csrf_exempt
def api_register(request):
    """
    API register untuk Flutter.
    Menerima data JSON untuk membuat user baru.
    """
    if request.method == 'POST':
        try:
            # Accept form-encoded POST or JSON body
            username = request.POST.get('username')
            password = request.POST.get('password')
            email = request.POST.get('email', '')

            if not username:
                try:
                    payload = json.loads(request.body.decode('utf-8') or '{}')
                except Exception:
                    payload = {}
                username = payload.get('username')
                password = payload.get('password')
                email = payload.get('email', '')

            # Validasi input
            if not username or not password:
                return JsonResponse({
                    "status": False,
                    "message": "Username dan password harus diisi."
                }, status=400)

            # Cek duplikasi username/email
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

            # Buat User Baru
            user = User.objects.create_user(username=username, password=password, email=email)
            user.save()

            # Buat UserProfile otomatis
            UserProfile.objects.create(user=user)

            # Auto-login (creates session cookie) - optional for mobile
            try:
                auth_login(request, user)
            except Exception:
                pass

            return JsonResponse({
                "status": True,
                "message": "Akun berhasil dibuat!",
                "username": user.username,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            }, status=201)

        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Terjadi kesalahan: {str(e)}"
            }, status=500)

    return JsonResponse({
        "status": False,
        "message": "Invalid request method."
    }, status=400)


@csrf_exempt
def api_logout(request):
    """
    API logout untuk Flutter.
    """
    if request.user.is_authenticated:
        username = request.user.username
        try:
            auth_logout(request)
            return JsonResponse({
                "status": True,
                "message": f"Logout berhasil! Sampai jumpa, {username}."
            }, status=200)
        except Exception as e:
            return JsonResponse({
                "status": False,
                "message": f"Logout gagal: {str(e)}"
            }, status=500)
            
    return JsonResponse({
        "status": True, # Tetap true agar flutter tidak error
        "message": "User sudah logout sebelumnya."
    }, status=200)


# ===================== Web Views (HTML) =====================

def register(request):
    """View Register untuk Web (HTML)"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Buat profile
            UserProfile.objects.create(user=user)
            
            # CATATAN: Kode penyimpanan ke 'users.json' dihapus 
            # karena menyebabkan error dan tidak diperlukan (data sudah masuk DB).
            
            messages.success(request, 'Akun berhasil dibuat! Silakan login.')
            return redirect('accounts:login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """View Login untuk Web (HTML)"""
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            
            # Redirect Logic: Admin ke Dashboard, User Biasa ke Home
            if user.is_staff or user.is_superuser:
                messages.success(request, f'Selamat datang kembali, Admin {user.username}!')
                # Pastikan URL name 'admin_sportpedia:dashboard' benar ada di urls.py admin
                return redirect('admin_sportpedia:dashboard') 
            else:
                messages.success(request, f'Selamat datang kembali, {user.username}!')
                return redirect('/') 
        else:
            messages.error(request, 'Username atau password salah.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """View Logout untuk Web (HTML)"""
    auth_logout(request)
    messages.success(request, "Berhasil logout.")
    return redirect('accounts:login')