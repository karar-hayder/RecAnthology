from django.contrib import admin

from .models import Book, Genre

admin.site.register(Genre)
admin.site.register(Book)
