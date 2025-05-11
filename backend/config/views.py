from django.http import HttpResponse
import requests

def landing(request):
    response = requests.get("http://localhost:3000/")
    return HttpResponse(response.content)
