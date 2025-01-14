# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # Inclure les URLs de l'application app
    path('', include('app.urls')),  # Assumant que votre application s'appelle 'app'
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # Pour gérer les fichiers média en développement

# Si vous êtes en mode DEBUG, ajoutez également le support des fichiers statiques
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)