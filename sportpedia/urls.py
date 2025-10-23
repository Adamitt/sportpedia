from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Landing page / beranda utama
    path('', include(('landingpage.urls', 'landingpage'), namespace='landingpage')),


    # App lain
    path('gearguide/', include(('gearguide.urls', 'gearguide'), namespace='gearguide')),
    path('sportlibrary/', include(('sportlibrary.urls', 'sportlibrary'), namespace='sportlibrary')),
    path('admin_sportpedia/', include(('admin_sportpedia.urls', 'admin_sportpedia'), namespace='admin_sportpedia')),
    path('profile/', include(('profile_app.urls', 'profile_app'), namespace='profile_app')),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('community/', include(('sportforum.urls', 'sportforum'), namespace='sportforum')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
