from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    preferred_language = models.CharField(max_length=10, choices=[
        ('fr', 'Français'),
        ('en', 'English'),
        ('lu', 'Luxembourgeois'),
        ('it', 'Italie'),
    ], default='fr')
    country = models.CharField(max_length=2, choices=[
        ('FR', 'France'),
        ('US', 'United States'),
        ('LU', 'Luxembourg'),
        ('it', 'Italia'),
    ], default='FR')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username