from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import landing

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", landing, name="landing"),
] + static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
