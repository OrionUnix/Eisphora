from django.shortcuts import redirect

def landing(request):
    return redirect(f"http://localhost:3000{request.path}")