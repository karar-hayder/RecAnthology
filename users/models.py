from django.apps import apps
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from Books.models import Book
from Books.models import Genre as BookGenre
from moviesNshows.models import Genre as TvGenre
from moviesNshows.models import TvMedia
from myutils.ExtraTools import scale


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):

        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    first_name = models.CharField(max_length=30, null=False, blank=False)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField("Email", blank=False, unique=True)
    username = None
    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]

    def __str__(self) -> str:
        return f"{self.get_full_name()}"

    from django.apps import apps
    from django.db import transaction

    def update_books_genre_preferences(self):
        cache.delete(f"{self.pk}_books_recomendation")
        UserBooksGenrePreference = apps.get_model("users", "UserBooksGenrePreference")
        ratings = (
            self.rated_books.select_related("book")
            .prefetch_related("book__genre")
            .all()
        )
        if not ratings.exists():
            return {}

        genre_ratings = {}
        for rating in ratings:
            for genre in rating.book.genre.all():
                if genre not in genre_ratings:
                    genre_ratings[genre] = {"weighted_sum": 0, "count": 0}
                genre_ratings[genre]["weighted_sum"] += rating.rating
                genre_ratings[genre]["count"] += 1

        genres_to_update = list(genre_ratings.keys())

        with transaction.atomic():
            # Fetch all existing prefs for user/these genres
            existing_prefs = UserBooksGenrePreference.objects.filter(
                user=self, genre__in=genres_to_update
            )
            existing_prefs_map = {pref.genre: pref for pref in existing_prefs}

            to_update = []
            to_create = []
            for genre, data in genre_ratings.items():
                # Cap percentage at 100 for safety
                percentage = min(
                    round((data["weighted_sum"] / data["count"]) * 10, 2), 100.0
                )
                perf = scale(percentage, (0, 100), (-5, 5))
                if genre in existing_prefs_map:
                    pref_obj = existing_prefs_map[genre]
                    if pref_obj.preference != perf:
                        pref_obj.preference = perf
                        to_update.append(pref_obj)
                else:
                    to_create.append(
                        UserBooksGenrePreference(
                            user=self, genre=genre, preference=perf
                        )
                    )

            if to_update:
                UserBooksGenrePreference.objects.bulk_update(to_update, ["preference"])
            if to_create:
                UserBooksGenrePreference.objects.bulk_create(to_create)

    def update_media_genre_preferences(self):
        cache.delete(f"{self.pk}_tvmedia_recomendation")
        UserTvMediaGenrePreference = apps.get_model(
            "users", "UserTvMediaGenrePreference"
        )
        ratings = (
            self.rated_tvmedia.select_related("tvmedia")
            .prefetch_related("tvmedia__genre")
            .all()
        )
        if not ratings.exists():
            return {}

        genre_ratings = {}
        for rating in ratings:
            for genre in rating.tvmedia.genre.all():
                if genre not in genre_ratings:
                    genre_ratings[genre] = {"weighted_sum": 0, "count": 0}
                genre_ratings[genre]["weighted_sum"] += rating.rating
                genre_ratings[genre]["count"] += 1

        genres_to_update = list(genre_ratings.keys())

        with transaction.atomic():
            existing_prefs = UserTvMediaGenrePreference.objects.filter(
                user=self, genre__in=genres_to_update
            )
            existing_prefs_map = {pref.genre: pref for pref in existing_prefs}

            to_update = []
            to_create = []
            for genre, data in genre_ratings.items():
                percentage = min(
                    round((data["weighted_sum"] / data["count"]) * 10, 2), 100.0
                )
                perf = scale(percentage, (0, 100), (-5, 5))
                if genre in existing_prefs_map:
                    pref_obj = existing_prefs_map[genre]
                    if pref_obj.preference != perf:
                        pref_obj.preference = perf
                        to_update.append(pref_obj)
                else:
                    to_create.append(
                        UserTvMediaGenrePreference(
                            user=self, genre=genre, preference=perf
                        )
                    )

            if to_update:
                UserTvMediaGenrePreference.objects.bulk_update(
                    to_update, ["preference"]
                )
            if to_create:
                UserTvMediaGenrePreference.objects.bulk_create(to_create)

    def get_books_genre_preferences(self):
        return {
            pref.genre: pref.preference
            for pref in self.books_genre_preferences.order_by("-preference")
        }

    def get_media_genre_preferences(self):
        return {
            pref.genre: pref.preference
            for pref in self.media_genre_preferences.order_by("-preference")
        }


class UserBookRating(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="rated_books"
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )  # 1 to 10

    class Meta:
        unique_together = ("user", "book")

    def clean(self):
        if not (1 <= self.rating <= 10):
            raise ValidationError(f"Rating must be between 1 and 10, got {self.rating}")


class UserBooksGenrePreference(models.Model):
    user = models.ForeignKey(
        CustomUser, related_name="books_genre_preferences", on_delete=models.CASCADE
    )
    genre = models.ForeignKey(BookGenre, on_delete=models.CASCADE)
    preference = models.FloatField()

    class Meta:
        unique_together = ("user", "genre")

    def __str__(self):
        return f"{self.genre.name}: {self.preference:.2f}%"


class UserTvMediaRating(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="rated_tvmedia"
    )
    tvmedia = models.ForeignKey(TvMedia, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )  # 1 to 10

    class Meta:
        unique_together = ("user", "tvmedia")

    def clean(self):
        if not (1 <= self.rating <= 10):
            raise ValidationError(f"Rating must be between 1 and 10, got {self.rating}")


class UserTvMediaGenrePreference(models.Model):
    user = models.ForeignKey(
        CustomUser, related_name="media_genre_preferences", on_delete=models.CASCADE
    )
    genre = models.ForeignKey(TvGenre, on_delete=models.CASCADE)
    preference = models.FloatField()

    class Meta:
        unique_together = ("user", "genre")

    def __str__(self):
        return f"{self.genre.name}: {self.preference:.2f}%"


@receiver(post_save, sender=UserBookRating)
def update_books_preferences(sender, instance, **kwargs):
    instance.user.update_books_genre_preferences()


@receiver(post_save, sender=UserTvMediaRating)
def update_media_preferences(sender, instance, **kwargs):
    instance.user.update_media_genre_preferences()
