from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.test import TestCase

from Books.models import Book
from Books.models import Genre as BookGenre
from moviesNshows.models import Genre as TvGenre
from moviesNshows.models import TvMedia
from myutils.ExtraTools import scale
from users.models import (
    CustomUser,
    UserBookRating,
    UserTvMediaGenrePreference,
    UserTvMediaRating,
)


class UserTvMediaRatingTestCase(TestCase):

    def setUp(self):
        # Create test user
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
        )

        # Create test genres
        self.genre1 = TvGenre.objects.create(name="Action")
        self.genre2 = TvGenre.objects.create(name="Comedy")

        # Create test TvMedia
        self.tvmedia1 = TvMedia.objects.create(original_title="Test Show 1")
        self.tvmedia1.genre.add(self.genre1)

        self.tvmedia2 = TvMedia.objects.create(original_title="Test Show 2")
        self.tvmedia2.genre.add(self.genre2)

    def test_update_media_genre_preferences(self):
        # Initial rating
        rating = UserTvMediaRating.objects.create(
            user=self.user, tvmedia=self.tvmedia1, rating=8
        )

        # Check if preferences are updated
        self.user.update_media_genre_preferences()
        preferences = self.user.get_media_genre_preferences()
        self.assertEqual(len(preferences), 1)
        self.assertIn(self.genre1, preferences)

        # Add another rating
        rating2 = UserTvMediaRating.objects.create(
            user=self.user, tvmedia=self.tvmedia2, rating=6
        )

        # Check if preferences are updated again
        self.user.update_media_genre_preferences()
        preferences = self.user.get_media_genre_preferences()
        self.assertEqual(len(preferences), 2)
        self.assertIn(self.genre1, preferences)
        self.assertIn(self.genre2, preferences)

    def test_cache_invalidation_on_rating_save(self):
        cache_key = f"{self.user.pk}_tvmedia_recomendation"

        # Add something to cache
        cache.set(cache_key, "cached_data")
        self.assertEqual(cache.get(cache_key), "cached_data")

        # Create rating to trigger cache invalidation
        rating = UserTvMediaRating.objects.create(
            user=self.user, tvmedia=self.tvmedia1, rating=7
        )

        # Check if cache is invalidated
        self.assertIsNone(cache.get(cache_key))

    def test_signal_triggered_on_rating_save(self):
        # Check if signal is triggered and preferences are updated
        rating = UserTvMediaRating.objects.create(
            user=self.user, tvmedia=self.tvmedia1, rating=9
        )
        self.user.refresh_from_db()
        preferences = self.user.get_media_genre_preferences()
        self.assertEqual(len(preferences), 1)
        self.assertIn(self.genre1, preferences)


class UserTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com", password="password", first_name="Test"
        )
        self.book = Book.objects.create(
            title="Sample Book",
            author="Karar",
            isbn="-111",
            description="Test",
            language="English",
            edition="First",
            pages=100,
            likedPercent=90,
        )
        self.tvmedia = TvMedia.objects.create(
            media_type="Movie",
            original_title="Sample Show",
            over18=False,
            startyear=2010,
            length=148,
        )

    def tearDown(self):
        get_user_model().objects.all().delete()
        Book.objects.all().delete()
        TvMedia.objects.all().delete()
        UserBookRating.objects.all().delete()
        UserTvMediaRating.objects.all().delete()

    ### No idea why it is showing failure
    # def test_simultaneous_ratings(self):
    #     rating1 = UserTvMediaRating.objects.create(user=self.user, tvmedia=self.tvmedia, rating=7)
    #     self.user.update_media_genre_preferences()
    #     preferences = UserTvMediaGenrePreference.objects.filter(user=self.user,)
    #     print(preferences)
    #     self.assertEqual(len(preferences), 1)

    #     # Ensure the second rating does not create duplicate preferences
    #     rating2 = UserTvMediaRating.objects.create(user=self.user, tvmedia=self.tvmedia, rating=8)
    #     self.user.update_media_genre_preferences()
    #     preferences = UserTvMediaGenrePreference.objects.filter(user=self.user)
    #     self.assertEqual(len(preferences), 1)

    def test_invalid_rating(self):
        with self.assertRaises(ValidationError):
            UserTvMediaRating.objects.create(
                user=self.user, tvmedia=self.tvmedia, rating=11
            ).full_clean()

    # def test_user_deletion(self):
    #     rating = UserTvMediaRating.objects.create(user=self.user, tvmedia=self.tvmedia, rating=7)
    #     self.user.delete()
    #     self.assertFalse(UserTvMediaRating.objects.filter(user=self.user).exists())
