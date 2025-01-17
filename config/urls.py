from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # Inclure les URLs de l'application app
    path('', include('app.urls')),  # Assumant que votre application s'appelle 'app'
]

# Configuration minimale pour les fichiers média en production
if settings.MEDIA_URL and settings.MEDIA_ROOT:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)