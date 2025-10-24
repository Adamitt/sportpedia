from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from .models import UserProfile, SportProgress
from profile_app.models import ActivityLog

@login_required(login_url='/accounts/login/')
def profile_page(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    recent_activities = ActivityLog.objects.filter(user=request.user).order_by('-timestamp')[:10]

    context = {
        'user': request.user,
        'profile': profile,
        'aktivitas': recent_activities,
    }
    return render(request, 'profile_app/profile.html', context)


@login_required(login_url='/accounts/login/')
def pengaturan_akun(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    user = request.user

    if request.method == 'POST':
        # --- Ambil semua field ---
        email = request.POST.get('email')
        new_password = request.POST.get('password')
        olahraga_favorit = request.POST.get('olahraga_favorit')
        preferensi = request.POST.get('preferensi')
        foto = request.FILES.get('foto_profil')

        # --- Update User ---
        if email and email != user.email:
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                messages.error(request, '❌ Email sudah digunakan.')
                return redirect('profile_app:pengaturan_akun')
            user.email = email

        if new_password:
            user.set_password(new_password)
            update_session_auth_hash(request, user)  # biar tetap login

        user.save()

        # --- Update Profile ---
        profile.olahraga_favorit = olahraga_favorit
        profile.preferensi = preferensi
        if foto:
            profile.foto_profil = foto
        profile.save()

        return redirect('profile_app:profile_page')

    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'profile_app/pengaturan_akun.html', context)

def profile_view(request):
    progress = SportProgress.objects.filter(user=request.user)

    total_time = 240
    for p in progress:
        percent = min(int((p.time_spent / total_time) * 100), 100)
        p.percent = percent

    context = {
        'profile': request.user.userprofile,
        'user': request.user,
        'progress': progress,
    }
    return render(request, 'profile_page/profile.html', context)