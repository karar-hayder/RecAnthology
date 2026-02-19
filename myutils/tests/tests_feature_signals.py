from django.contrib.auth import get_user_model
from django.test import TestCase

from Books.models import Book
from Books.models import Genre as BookGenre
from moviesNshows.models import Genre as TvGenre
from moviesNshows.models import TvMedia
from myutils.feature_signals import (
    MAX_SIGNAL_BONUS,
    compute_author_affinity,
    compute_language_preference,
    compute_media_type_bonus,
    compute_popularity_bonus,
    compute_recency_bonus,
    compute_signal_bonus,
)
from users.models import UserBookRating, UserTvMediaRating

User = get_user_model()


class FeatureSignalsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="password", first_name="Test"
        )
        self.genre_book = BookGenre.objects.create(name="Fiction")
        self.genre_tv = TvGenre.objects.create(name="Sci-Fi")

    def test_popularity_bonus(self):
        book = Book.objects.create(
            title="Popular Book",
            author="Author A",
            isbn="123",
            pages=100,
            likedPercent=90,
        )
        bonus = compute_popularity_bonus(book)
        self.assertEqual(bonus, 0.9)

        unpopular_book = Book.objects.create(
            title="Unpopular Book",
            author="Author B",
            isbn="456",
            pages=100,
            likedPercent=10,
        )
        bonus = compute_popularity_bonus(unpopular_book)
        self.assertEqual(bonus, 0.1)

    def test_author_affinity(self):
        # Create books by same author
        book1 = Book.objects.create(
            title="Book 1", author="Author X", isbn="X1", pages=100, likedPercent=50
        )
        book2 = Book.objects.create(
            title="Book 2", author="Author X", isbn="X2", pages=100, likedPercent=50
        )
        target_book = Book.objects.create(
            title="Target", author="Author X", isbn="TX", pages=100, likedPercent=50
        )

        # Rate 2 books by Author X highly
        UserBookRating.objects.create(user=self.user, book=book1, rating=8)
        UserBookRating.objects.create(user=self.user, book=book2, rating=9)

        bonus = compute_author_affinity(target_book, self.user, UserBookRating, "book")
        self.assertEqual(bonus, 1.0)

        # Different author should have 0 bonus
        other_book = Book.objects.create(
            title="Other", author="Author Y", isbn="Y1", pages=100, likedPercent=50
        )
        bonus = compute_author_affinity(other_book, self.user, UserBookRating, "book")
        self.assertEqual(bonus, 0.0)

    def test_language_preference(self):
        # Rate high in English
        book_en = Book.objects.create(
            title="EN",
            author="A",
            isbn="EN1",
            pages=100,
            likedPercent=50,
            language="English",
        )
        UserBookRating.objects.create(user=self.user, book=book_en, rating=10)

        target_en = Book.objects.create(
            title="EN2",
            author="A",
            isbn="EN2",
            pages=100,
            likedPercent=50,
            language="English",
        )
        bonus = compute_language_preference(
            target_en, self.user, UserBookRating, "book"
        )
        self.assertEqual(bonus, 1.0)

        target_fr = Book.objects.create(
            title="FR",
            author="A",
            isbn="FR1",
            pages=100,
            likedPercent=50,
            language="French",
        )
        bonus = compute_language_preference(
            target_fr, self.user, UserBookRating, "book"
        )
        self.assertEqual(bonus, 0.0)

    def test_recency_bonus(self):
        # 2026 is max_year, 1970 is min_year
        recent_tv = TvMedia.objects.create(
            original_title="Recent", media_type="movie", startyear=2020
        )
        bonus = compute_recency_bonus(recent_tv)
        # (2020-1970)/(2026-1970) = 50/56 approx 0.89
        self.assertAlmostEqual(bonus, 50 / 56, places=2)

        old_tv = TvMedia.objects.create(
            original_title="Old", media_type="movie", startyear=1980
        )
        bonus = compute_recency_bonus(old_tv)
        # (1980-1970)/56 = 10/56 approx 0.178
        self.assertAlmostEqual(bonus, 10 / 56, places=2)

    def test_media_type_bonus(self):
        # Rate high for movies
        tv1 = TvMedia.objects.create(
            original_title="Movie 1", media_type="movie", startyear=2000
        )
        UserTvMediaRating.objects.create(user=self.user, tvmedia=tv1, rating=9)

        target_movie = TvMedia.objects.create(
            original_title="Movie 2", media_type="movie", startyear=2000
        )
        bonus = compute_media_type_bonus(
            target_movie, self.user, UserTvMediaRating, "tvmedia"
        )
        self.assertEqual(bonus, 1.0)

        target_show = TvMedia.objects.create(
            original_title="Show 1", media_type="tvSeries", startyear=2000
        )
        bonus = compute_media_type_bonus(
            target_show, self.user, UserTvMediaRating, "tvmedia"
        )
        self.assertEqual(bonus, 0.0)

    def test_signal_bonus_cap(self):
        # High popularity (1.0 * 10 = 10) + Author affinity (1.0 * 12 = 12) + Language (1.0 * 5 = 5) + Recency (high)
        # Let's say we have 37 points total. It should be capped at 30.
        book = Book.objects.create(
            title="Super Book",
            author="Author X",
            isbn="SX",
            pages=100,
            likedPercent=100,
            language="English",
        )
        # Setup author affinity (2 high ratings for Author X)
        b1 = Book.objects.create(
            title="B1",
            author="Author X",
            isbn="BX1",
            pages=100,
            likedPercent=50,
            language="English",
        )
        b2 = Book.objects.create(
            title="B2",
            author="Author X",
            isbn="BX2",
            pages=100,
            likedPercent=50,
            language="English",
        )
        UserBookRating.objects.create(user=self.user, book=b1, rating=9)
        UserBookRating.objects.create(user=self.user, book=b2, rating=9)
        # Setup language preference (High rating for English)
        b_en = Book.objects.create(
            title="EN",
            author="A",
            isbn="LX",
            language="English",
            pages=100,
            likedPercent=50,
        )
        UserBookRating.objects.create(user=self.user, book=b_en, rating=9)

        total_bonus = compute_signal_bonus(book, self.user, UserBookRating, "book")
        # Calc: Pop(1.0*10) + Author(1.0*12) + Lang(1.0*5) = 27 (less than 30)
        self.assertEqual(total_bonus, 27.0)

        # Now override weights to exceed 30
        custom_weights = {"popularity": 20.0, "author_affinity": 20.0}
        total_bonus = compute_signal_bonus(
            book, self.user, UserBookRating, "book", weights=custom_weights
        )
        self.assertEqual(total_bonus, MAX_SIGNAL_BONUS)
