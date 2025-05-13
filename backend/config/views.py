from django.http import HttpResponse
import requests
import os

def landing(request):
    NEXTJS_URL = os.getenv('NEXTJS_URL', 'http://localhost:3000')
    next_url = f"{NEXTJS_URL}{request.path}"
    response = requests.get(next_url)
    content = response.content.decode('utf-8')
    content = content.replace('/_next/', f'{NEXTJS_URL}/_next/')
    content = content.replace('/icons/', f'{NEXTJS_URL}/icons/')
    return HttpResponse(content, content_type=response.headers['content-type'])