from django.db import models
from django.contrib.auth.models import User

class Collection(models.Model):
    title = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Video(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField()
    youtube_id = models.CharField(max_length=100)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)

