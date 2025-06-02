from django.views.generic import TemplateView
from django.utils.translation import get_language

class HomeView(TemplateView):
    template_name = 'home.html'
