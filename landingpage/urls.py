# landingpage/urls.py
from django.urls import path
from . import views

app_name = "landingpage"

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    # API testimonials
    path("api/testimonials/", views.api_testimonials_list, name="api_testimonials_list"),
    path("api/testimonials/create/", views.api_testimonials_create, name="api_testimonials_create"),
    path("api/testimonials/<int:pk>/update/", views.api_testimonials_update, name="api_testimonials_update"),
    path("api/testimonials/<int:pk>/delete/", views.api_testimonials_delete, name="api_testimonials_delete"),
    path(
        "api/popular-categories/",
        views.api_popular_categories,
        name="api_popular_categories",
    ),
    # API search
    path("api/search/", views.api_search, name="api_search"),
    # API untuk get CSRF token
    path("api/csrf-token/", views.api_csrf_token, name="api_csrf_token"),
    # path("whats-hot/", views.whats_hot, name="whats_hot"),
]
