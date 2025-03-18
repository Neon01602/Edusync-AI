from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    profile_picture = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.username
# Create your models here.

from django.db import models
from django.contrib.auth.models import User

class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

from django.conf import settings
from django.db import models

import random
import string
from django.db import models
from django.conf import settings

def generate_unique_code():
    """Generate a random 6-character code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class Classroom(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_classes")
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="joined_classes", blank=True)
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    unique_code = models.CharField(max_length=10, unique=True, blank=True, default=generate_unique_code)

    def __str__(self):
        return f"{self.name} ({self.subject}) - {self.teacher.username}"


    def save(self, *args, **kwargs):
        if not self.unique_code:
            import random, string
            self.unique_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        super().save(*args, **kwargs)

class Classwork(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="classworks")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assigned_classwork")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='classwork_files/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} - {self.classroom.name} ({self.teacher.username})"