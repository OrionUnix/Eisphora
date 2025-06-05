from django.urls import path
from . import views

app_name = 'tax_forms'

urlpatterns = [
    path('form-2048/', views.form_2048_view, name='form_2048'),
]