from django.http import HttpResponse
import requests
import os

def landing(request):
    next_url = f"http://localhost:3000{request.path}"
    try:
        response = requests.get(next_url)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '')
        if 'text/html' in content_type:
            content = response.content.decode('utf-8')
            # Réécrire les URLs pour pointer vers Django
            content = content.replace('/_next/', '/static/_next/')
            content = content.replace('/icons/', '/static/icons/')
        else:
            content = response.content
        return HttpResponse(content, content_type=content_type)
    except requests.RequestException as e:
        return HttpResponse(f"Error fetching Next.js page: {e}", status=500)