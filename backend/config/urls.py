from django.contrib import admin
from django.urls import path, re_path
from .views import landing
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    re_path(r'^.*$', landing, name="landing"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)