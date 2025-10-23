from django.urls import path
from . import views

app_name = "gearguide"

urlpatterns = [
    path("", views.show_all_gears, name="show_all_gears"),
    path("<int:gear_id>/", views.card_details, name="card_details"),
    path("add/", views.add_gear, name="add_gear"),

]
