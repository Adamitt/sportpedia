from django.urls import path
from . import views

app_name = "sportforum"

urlpatterns = [
    path("", views.show_forum, name="show_forum"),
    path("create-ajax/", views.add_post_ajax, name="add_post_ajax"),  # AJAX create post
    path("post/<str:id>/", views.post_detail, name="post_detail"),
    path("post/<str:id>/like", views.toggle_like, name="toggle_like"),
    path("post/<str:id>/edit", views.edit_post, name="edit_post"),
    path("post/<str:id>/delete", views.delete_post, name="delete_post"),
    path("post/json/<str:id>/", views.show_json_by_id, name="show_json_by_id"),
    path("json/", views.show_json, name="show_json"),
    path("create-forum-flutter/", views.create_forum_flutter, name="create_forum_flutter"),
    path("post/<str:id>/like-flutter", views.toggle_like_flutter, name="toggle_like_flutter"),
    path("post/<str:id>/reply-flutter", views.post_reply_flutter, name="post_reply_flutter"),
    path("post/<str:id>/edit-flutter", views.edit_post_flutter, name="edit_post_flutter"),
    path("post/<str:id>/delete-flutter", views.delete_post_flutter, name="delete_post_flutter"),
]
