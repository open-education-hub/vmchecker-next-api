from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from api.views import api_definition

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_definition)),
    path('', include('django_prometheus.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
