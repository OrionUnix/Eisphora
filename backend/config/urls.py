from django.contrib import admin
from django.urls import path
from .views import HomeView
from django.urls import path, include

# Vue principale pour la page d'accueil

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('auth/', include('members.urls')),
]