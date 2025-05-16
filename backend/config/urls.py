from django.contrib import admin
from django.urls import path
from . import views

# Vue principale pour la page d'accueil

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),

]
