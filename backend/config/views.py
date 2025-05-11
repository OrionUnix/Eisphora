from django.http import HttpResponse
import requests

def landing(request):
    # Construire l'URL de Next.js
    next_url = f"http://localhost:3000{request.path}"
    response = requests.get(next_url)
    # Remplacer les URLs relatives par des URLs absolues
    content = response.content.decode('utf-8')
    content = content.replace('/_next/', 'http://localhost:3000/_next/')
    return HttpResponse(content, content_type=response.headers['content-type'])