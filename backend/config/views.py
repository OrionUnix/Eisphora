from django.http import HttpResponse
import requests

def landing(request):
    next_url = f"http://localhost:3000{request.path}"
    response = requests.get(next_url)
    content = response.content.decode('utf-8')
    # Remplacements pour couvrir plus de cas
    content = content.replace('/_next/', 'http://localhost:3000/_next/')
    content = content.replace('href="/', 'href="http://localhost:3000/')
    content = content.replace('src="/', 'src="http://localhost:3000/')
    content = content.replace('"/_next/', '"http://localhost:3000/_next/')
    content = content.replace('"/parallax/', '"http://localhost:3000/parallax/')
    # Ajouter pour les polices ou autres actifs potentiels
    content = content.replace('url(/', 'url(http://localhost:3000/')
    return HttpResponse(content, content_type=response.headers['content-type'])
