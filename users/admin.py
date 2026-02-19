from django.contrib import admin

from .models import (
    CustomUser,
    UserBookRating,
    UserBooksGenrePreference,
    UserTvMediaGenrePreference,
    UserTvMediaRating,
)

admin.site.register(CustomUser)
admin.site.register(UserBooksGenrePreference)
admin.site.register(UserBookRating)
admin.site.register(UserTvMediaGenrePreference)
admin.site.register(UserTvMediaRating)
