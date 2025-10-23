from django.urls import path
from . import views

urlpatterns = [
    path('', views.profile_page, name='profile_page'),
    path('pengaturan/', views.pengaturan_akun, name='pengaturan_akun'),
]
