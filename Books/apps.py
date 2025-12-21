from django.apps import AppConfig
from django.core.cache import cache


class BooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "Books"

    def ready(self) -> None:
        cache.clear()
        return super().ready()
