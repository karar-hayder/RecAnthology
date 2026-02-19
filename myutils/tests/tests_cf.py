from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from Books.models import Book, Genre
from myutils.collaborative_filtering import (
    _similarity_cache_key,
    calculate_cosine_similarity,
    get_collaborative_recommendations,
    get_item_similarities,
    invalidate_similarity_cache,
)
from myutils.recommendation import compute_adaptive_alpha, get_hybrid_recommendation
from users.models import CustomUser, UserBookRating


class CollaborativeFilteringTests(TestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            email="user9991@example.com", password="password", first_name="User1"
        )
        self.user2 = CustomUser.objects.create_user(
            email="user9992@example.com", password="password", first_name="User2"
        )
        self.user3 = CustomUser.objects.create_user(
            email="user9993@example.com", password="password", first_name="User3"
        )

        self.genre1 = Genre.objects.create(name="Genre1")

        self.book1 = Book.objects.create(
            title="Book1", author="Author1", isbn="1", pages=100, likedPercent=90
        )
        self.book1.genre.add(self.genre1)
        self.book2 = Book.objects.create(
            title="Book2", author="Author2", isbn="2", pages=100, likedPercent=90
        )
        self.book2.genre.add(self.genre1)
        self.book3 = Book.objects.create(
            title="Book3", author="Author3", isbn="3", pages=100, likedPercent=90
        )
        self.book3.genre.add(self.genre1)

        # User1 rates Book1 and Book2 high
        UserBookRating.objects.create(user=self.user1, book=self.book1, rating=9)
        UserBookRating.objects.create(user=self.user1, book=self.book2, rating=10)

        # User2 rates Book1 high and Book2 high
        UserBookRating.objects.create(user=self.user2, book=self.book1, rating=8)
        UserBookRating.objects.create(user=self.user2, book=self.book2, rating=9)

        # User3 rates Book1 high
        UserBookRating.objects.create(user=self.user3, book=self.book1, rating=10)

    def test_cosine_similarity(self):
        r1 = {1: 9, 2: 8}
        r2 = {1: 10, 2: 9}
        sim = calculate_cosine_similarity(r1, r2)
        self.assertGreater(sim, 0.9)

    def test_item_similarities(self):
        sims = get_item_similarities(self.book1.id, UserBookRating, "book")
        # Book2 should be similar to Book1 because User1 and User2 rated both
        self.assertTrue(any(item_id == self.book2.id for _, item_id in sims))

    def test_collaborative_recommendations(self):
        # User3 rated Book1, should get Book2 as recommendation
        recs = get_collaborative_recommendations(
            self.user3, UserBookRating, Book, "book"
        )
        self.assertTrue(any(item.id == self.book2.id for _, item in recs))

    def test_hybrid_recommendation(self):
        # Should combine genre and collaborative
        needed = {self.genre1: 5.0}
        recs = get_hybrid_recommendation(
            user=self.user3,
            user_needed_genres=needed,
            interaction_model=UserBookRating,
            item_model=Book,
            item_field="book",
        )
        self.assertTrue(len(recs) > 0)
        # Check that Book2 is in the list
        self.assertTrue(any(item.id == self.book2.id for _, item in recs))


class AdaptiveAlphaTests(TestCase):
    def test_low_ratings_high_alpha(self):
        """User with very few ratings → α close to 1.0 (content-heavy)."""
        alpha = compute_adaptive_alpha(rating_count=2, cf_weight=0.4, threshold=15)
        self.assertGreater(alpha, 0.9)

    def test_high_ratings_low_alpha(self):
        """User with many ratings → α = 1.0 - cf_weight (full hybrid)."""
        alpha = compute_adaptive_alpha(rating_count=30, cf_weight=0.4, threshold=15)
        self.assertAlmostEqual(alpha, 0.6)

    def test_zero_ratings(self):
        """User with 0 ratings → pure content-based (α = 1.0)."""
        alpha = compute_adaptive_alpha(rating_count=0, cf_weight=0.4, threshold=15)
        self.assertAlmostEqual(alpha, 1.0)

    def test_at_threshold(self):
        """At exactly threshold ratings → α = 1.0 - cf_weight."""
        alpha = compute_adaptive_alpha(rating_count=15, cf_weight=0.4, threshold=15)
        self.assertAlmostEqual(alpha, 0.6)

    def test_hybrid_with_adaptive_alpha(self):
        """Hybrid recommendation with adaptive alpha produces results."""
        genre = Genre.objects.create(name="AdaptiveGenre")
        user = CustomUser.objects.create_user(
            email="adaptive@example.com", password="password", first_name="Adaptive"
        )
        book = Book.objects.create(
            title="AdaptiveBook", author="A", isbn="adapt-1", pages=100, likedPercent=80
        )
        book.genre.add(genre)

        recs = get_hybrid_recommendation(
            user=user,
            user_needed_genres={genre: 5.0},
            interaction_model=UserBookRating,
            item_model=Book,
            item_field="book",
            rating_count=5,
        )
        self.assertIsInstance(recs, list)


class SimilarityCacheTests(TestCase):
    def setUp(self):
        cache.clear()
        self.genre = Genre.objects.create(name="CacheGenre")
        self.user1 = CustomUser.objects.create_user(
            email="cache1@example.com", password="password", first_name="Cache1"
        )
        self.user2 = CustomUser.objects.create_user(
            email="cache2@example.com", password="password", first_name="Cache2"
        )
        self.book1 = Book.objects.create(
            title="CacheBook1", author="A", isbn="cache-1", pages=100, likedPercent=80
        )
        self.book1.genre.add(self.genre)
        self.book2 = Book.objects.create(
            title="CacheBook2", author="A", isbn="cache-2", pages=100, likedPercent=80
        )
        self.book2.genre.add(self.genre)
        UserBookRating.objects.create(user=self.user1, book=self.book1, rating=9)
        UserBookRating.objects.create(user=self.user1, book=self.book2, rating=8)
        UserBookRating.objects.create(user=self.user2, book=self.book1, rating=7)

    def test_similarity_cache_hit(self):
        """Second call should return cached result."""
        # First call populates cache
        result1 = get_item_similarities(self.book1.id, UserBookRating, "book")
        key = _similarity_cache_key("book", self.book1.id)
        cached = cache.get(key)
        self.assertIsNotNone(cached)
        self.assertEqual(result1, cached)

    def test_similarity_cache_invalidation(self):
        """Cache should be cleared after invalidation."""
        # Populate cache
        get_item_similarities(self.book1.id, UserBookRating, "book")
        key = _similarity_cache_key("book", self.book1.id)
        self.assertIsNotNone(cache.get(key))

        # Invalidate
        invalidate_similarity_cache("book", self.book1.id)
        self.assertIsNone(cache.get(key))
