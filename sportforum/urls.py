from django.urls import path
from . import views

app_name = "sportforum"

urlpatterns = [
    path("", views.show_forum, name="show_forum"),
    path("post/<str:id>/", views.post_detail, name="post_detail"),
    path("new/", views.new_post, name="new_post"),  # Removed category_slug parameter
    path("post/<str:id>/like", views.toggle_like, name="toggle_like"),
    path("post/<str:id>/edit", views.edit_post, name="edit_post"),
    path("post/<str:id>/delete", views.delete_post, name="delete_post"),
    path("json/", views.show_json, name="show_json"),
    path("post/json/<str:id>/", views.show_json_by_id, name="show_json_by_id"),
]
