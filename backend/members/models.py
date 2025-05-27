from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    pass  # No additional fields, inherits from AbstractUser

class UserProfile(models.Model):
    user = models.OneToOneField('CustomUser', on_delete=models.CASCADE)
    country = models.CharField(max_length=2, choices=[('FR', 'France'), ('US', 'United States')])

    def __str__(self):
        return self.user.username