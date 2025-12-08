from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from .models import UserProfile
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
        email = request.POST.get('email')
        new_password = request.POST.get('password')
        olahraga_favorit = request.POST.get('olahraga_favorit')
        preferensi = request.POST.get('preferensi')
        foto_url = request.POST.get('foto_profil')

        if email and email != user.email:
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                messages.error(request, '❌ Email sudah digunakan.')
                return redirect('profile_app:pengaturan_akun')
            user.email = email

        if new_password:
            user.set_password(new_password)
            update_session_auth_hash(request, user)

        user.save()

        profile.olahraga_favorit = olahraga_favorit
        profile.preferensi = preferensi
        if foto_url:
            profile.foto_profil = foto_url
        profile.save()

        return redirect('profile_app:profile_page')

    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'profile_app/pengaturan_akun.html', context)

def profile_view(request):
    context = {
        'profile': request.user.userprofile,
        'user': request.user,
    }
    return render(request, 'profile_page/profile.html', context)