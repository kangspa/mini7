from django.db import models

# Create your models here.
class Chats(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    question = models.TextField()
    result = models.TextField()
    username = models.CharField(max_length=30)