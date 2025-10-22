from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import UserProfile, ProgressTracker, ActivityLog

@login_required(login_url='/accounts/login/')
def profile_page(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    progress_list = ProgressTracker.objects.filter(user=request.user)
    aktivitas_list = ActivityLog.objects.filter(user=request.user).order_by('-waktu')

    context = {
        'user': request.user,
        'profile': profile,
        'progress_list': progress_list,
        'aktivitas_list': aktivitas_list,
    }
    return render(request, 'profile_app/profile.html', context)

def pengaturan_akun(request):
    return render(request, 'profile_app/pengaturan_akun.html')