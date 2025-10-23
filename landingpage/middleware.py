# landingpage/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from django.conf import settings
from .models import PageHit

class PageHitMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        # catat hanya GET
        if request.method != "GET":
            return None
        try:
            match = resolve(request.path_info)
            view_name = match.view_name or ""
        except Exception:
            return None

        tracked = getattr(settings, "TRACKED_VIEWS", set())
        if view_name in tracked:
            obj, _ = PageHit.objects.get_or_create(
                view_name=view_name,
                path=request.path,
                defaults={"hits": 0}
            )
            obj.hits += 1
            obj.save(update_fields=["hits", "last_hit"])
        return None
