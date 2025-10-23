# gearguide/urls.py
from django.urls import path
from . import views

app_name = "gearguide"

urlpatterns = [
    path("", views.show_all_gears, name="show_all_gears"),
    path("add/", views.add_gear, name="add_gear"),
    
    # API endpoints
    path("api/gear/<str:gear_id>/", views.get_gear_json, name="get_gear_json"),
    path("api/gear/<str:gear_id>/edit/", views.edit_gear_ajax, name="edit_gear_ajax"),
    
    # Actions
    path("delete/<str:gear_id>/", views.delete_gear, name="delete_gear"),
    
    # Detail (catch-all)
    path("<str:gear_id>/", views.card_details, name="card_details"),
]
