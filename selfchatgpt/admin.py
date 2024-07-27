from django.contrib import admin
from .models import Chats

# Register your models here.
@admin.register(Chats)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['time', 'question', 'result']
    list_display_links = ['time', 'question', 'result']
    ordering = ['time']