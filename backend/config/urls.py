from django.contrib import admin
from django.urls import path
from .views import HomeView
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView

urlpatterns = [
   path('', RedirectView.as_view(url='/fr-fr/', permanent=False)),

]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('auth/', include('members.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
)