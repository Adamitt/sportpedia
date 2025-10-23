from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Beranda & halaman utama project (pakai app kamu)
    path('', include(('mainPage.urls', 'mainPage'), namespace='mainPage')),

    # App teman-teman
    path('sportlibrary/', include(('sportlibrary.urls', 'sportlibrary'), namespace='sportlibrary')),
    path('gearguide/', include(('gearguide.urls', 'gearguide'), namespace='gearguide')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
