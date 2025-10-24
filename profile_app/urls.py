from django.urls import path
from . import views

app_name = 'profile_app'

urlpatterns = [
    path('', views.profile_page, name='profile_page'),
    path('pengaturan/', views.pengaturan_akun, name='pengaturan_akun'),
]
