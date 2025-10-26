from django.urls import path
from . import views

app_name = "sportforum"

urlpatterns = [
    path("", views.show_forum, name="show_forum"),
    path("post/<str:id>/", views.post_detail, name="post_detail"),
    path("create-ajax/", views.add_post_ajax, name="add_post_ajax"),  # AJAX create post
    path("post/<str:id>/like", views.toggle_like, name="toggle_like"),
    path("post/<str:id>/edit", views.edit_post, name="edit_post"),
    path("post/<str:id>/delete", views.delete_post, name="delete_post"),
    path("json/", views.show_json, name="show_json"),
    path("post/json/<str:id>/", views.show_json_by_id, name="show_json_by_id"),
]
