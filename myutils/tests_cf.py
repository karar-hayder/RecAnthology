from django.test import TestCase

from Books.models import Book, Genre
from myutils.collaborative_filtering import (
    calculate_cosine_similarity,
    get_collaborative_recommendations,
    get_item_similarities,
)
from myutils.recommendation import get_hybrid_recommendation
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
        print(sims)
        self.assertTrue(any(item_id == self.book2.id for _, item_id in sims))

    def test_collaborative_recommendations(self):
        # User3 rated Book1, should get Book2 as recommendation
        recs = get_collaborative_recommendations(
            self.user3, UserBookRating, Book, "book"
        )
        print(recs)
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
        print(recs)
        self.assertTrue(len(recs) > 0)
        # Check that Book2 is in the list
        self.assertTrue(any(item.id == self.book2.id for _, item in recs))
