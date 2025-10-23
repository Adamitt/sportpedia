from django.db.models import F
from django.utils import timezone
from .models import ViewCounter

def bump_view(key, *, title, url, category, image=None, request=None, dedupe_seconds=900):
    """
    Tambah 1 view utk suatu 'key' (halaman).
    Dedupe per-session (default 15 menit) supaya nggak ke-spam refresh.
    """
    if request is not None and hasattr(request, "session"):
        sess_key = f"hit:{key}"
        now_ts = timezone.now().timestamp()
        last = request.session.get(sess_key)
        if last and (now_ts - last) < dedupe_seconds:
            return
        request.session[sess_key] = now_ts

    obj, created = ViewCounter.objects.get_or_create(
        key=key,
        defaults={
            "title": title[:200],
            "url": url[:300],
            "category": category[:50],
            "image": (image or "")[:500],
        },
    )
    if created:
        ViewCounter.objects.filter(pk=obj.pk).update(views=F("views") + 1)
    else:
        updates = {"views": F("views") + 1, "category": category[:50]}
        if title: updates["title"] = title[:200]
        if url:   updates["url"]   = url[:300]
        if image: updates["image"] = image[:500]
        ViewCounter.objects.filter(pk=obj.pk).update(**updates)
