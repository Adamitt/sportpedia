from django.urls import path
from . import views

app_name = 'sportlibrary'

urlpatterns = [
    # Web URLs (Django Template)
    path('', views.show_sports, name='show_sports'),
    path('saved/', views.saved_sports, name='saved_sports'),
    path('<int:sport_id>/save/', views.save_sport, name='save_sport'),
    path('saved/<int:saved_id>/remove/', views.remove_sport, name='remove_sport'),
    path('saved/clear/', views.clear_all_sports, name='clear_all_sports'),
    path('<int:sport_id>/', views.sport_detail, name='sport_detail'),

    # Flutter / Mobile API endpoints
    path('api/show-sports-json/', views.show_sports_json, name='show_sports_json'),
    path('api/sport-detail-json/<int:sport_id>/', views.sport_detail_json, name='sport_detail_json'),
    path('api/create-sport-flutter/', views.create_sport_flutter, name='create_sport_flutter'),
    path('api/edit-sport-flutter/<int:sport_id>/', views.edit_sport_flutter, name='edit_sport_flutter'),
    path('api/delete-sport-flutter/<int:sport_id>/', views.delete_sport_flutter, name='delete_sport_flutter'),
]
