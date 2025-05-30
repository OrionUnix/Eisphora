from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm
from .models import UserProfile


def sign_up(request):
    print("Request method:", request.method)
    print("POST data:", request.POST)
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        print("Form is valid:", form.is_valid(), "Errors:", form.errors)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'sign_up.html', {'form': form})

@login_required
def dashboard(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.country == 'FR':
            return redirect('fr_space')
        elif profile.country == 'US':
            return redirect('us_space')
    except UserProfile.DoesNotExist:
        return render(request, 'dashboard.html')
    return render(request, 'dashboard.html')

@login_required
def fr_space(request):
    return render(request, 'fr_space.html')

@login_required
def us_space(request):
    return render(request, 'us_space.html')

def logout_view(request):
    logout(request)
    return redirect('login')


