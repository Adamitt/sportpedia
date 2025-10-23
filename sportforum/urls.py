from django.urls import path
from . import views

app_name = "sportforum"

urlpatterns = [
    path("", views.show_forum, name="show_forum"),
    path("post/<str:id>/", views.post_detail, name="post_detail"),
    path("new/<str:category_slug>/", views.new_post, name="new_post"),
    path("like/<str:id>/", views.toggle_like, name="toggle_like"),
    path("post/<str:id>/edit", views.edit_post, name="edit_post"),
    path("post/<str:id>/delete", views.delete_post, name="delete_post"),
]
