from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.urls import path, include

urlpatterns = [
    path('sign_up/', views.sign_up, name='sign_up'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('fr_space/', views.fr_space, name='fr_space'),
    path('us_space/', views.us_space, name='us_space'),

]