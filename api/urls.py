from django.contrib import admin
from django.urls import path, include

from api.views import api_definition


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_definition)),
]