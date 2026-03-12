from django.urls import path
from .views import HomeView
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from django.shortcuts import render

# Débogage pour vérifier les URLs
print("Chargement des URLs principales")

urlpatterns = [
    path('', RedirectView.as_view(url='/fr-fr/', permanent=False)),
]
def terms_view(request):
    return render(request, 'pages/terms.html') 

urlpatterns += i18n_patterns(
    path('', HomeView.as_view(), name='home'),
    # auth/ routes removed for anonymity
    path('i18n/', include('django.conf.urls.i18n')),
    path('tax/', include('tax_forms.urls', namespace='tax_forms')),
    path('terms/', terms_view, name='terms'),
)