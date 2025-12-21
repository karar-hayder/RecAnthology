import uuid

# from django.contrib.auth import get_user_model
from django.db import models


class Genre(models.Model):
    name = models.CharField("name", max_length=50, blank=False, null=False)

    def __str__(self) -> str:
        return self.name


class Book(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, unique=True, primary_key=True, editable=False
    )
    title = models.CharField("title", max_length=300, blank=False, null=False)
    author = models.CharField("author", max_length=300, blank=False, null=False)
    genre = models.ManyToManyField(Genre, related_name="books")
    isbn = models.CharField("isbn", max_length=100, blank=False, null=False)
    description = models.CharField(
        "description", max_length=5000, blank=False, null=False
    )
    language = models.CharField("language", max_length=50, blank=False, null=False)
    edition = models.CharField(
        "edition", max_length=500, blank=False, null=False, default="First edition"
    )
    pages = models.PositiveIntegerField("pages", blank=False, null=False)
    likedPercent = models.IntegerField("likedPercent", blank=False, null=False)
    cover_image = models.ImageField(
        "Cover Image", upload_to="book_covers/", default="book_covers/default_cover.jpg"
    )

    def __str__(self) -> str:
        return f"{self.title}:{self.isbn}:{self.edition} -- {self.id}"
