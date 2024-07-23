from django.contrib import admin
from .models import CustomUser,UserBookRating,UserGenrePreference

admin.site.register(CustomUser)
admin.site.register(UserGenrePreference)
admin.site.register(UserBookRating)