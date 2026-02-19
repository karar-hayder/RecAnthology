from django.test import TestCase

from Books.models import Book, Genre
from myutils.cold_start import boost_new_items, get_popular_by_genre
from users.models import CustomUser, UserBookRating


class GetPopularByGenreTests(TestCase):
    def setUp(self):
        self.genre1 = Genre.objects.create(name="ColdGenre1")
        self.genre2 = Genre.objects.create(name="ColdGenre2")

        self.book1 = Book.objects.create(
            title="Popular Book",
            author="Author1",
            isbn="cs-1",
            description="Desc",
            language="English",
            pages=200,
            likedPercent=95,
        )
        self.book1.genre.add(self.genre1)

        self.book2 = Book.objects.create(
            title="Less Popular Book",
            author="Author2",
            isbn="cs-2",
            description="Desc",
            language="English",
            pages=150,
            likedPercent=60,
        )
        self.book2.genre.add(self.genre2)

        self.book3 = Book.objects.create(
            title="No Genre Match Book",
            author="Author3",
            isbn="cs-3",
            description="Desc",
            language="English",
            pages=100,
            likedPercent=80,
        )
        # book3 has no genre — won't match any preference

    def test_new_user_gets_popular_items(self):
        """User with 0 ratings gets popularity-sorted results."""
        results = get_popular_by_genre(
            item_model=Book,
            genre_prefs={self.genre1: 5.0},
            limit=10,
        )
        self.assertTrue(len(results) > 0)
        # Results should be sorted by score descending
        scores = [s for s, _ in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_global_fallback_when_no_prefs(self):
        """When genre_prefs is empty, returns global popularity."""
        results = get_popular_by_genre(
            item_model=Book,
            genre_prefs={},
            limit=10,
        )
        self.assertTrue(len(results) > 0)

    def test_genre_filtering(self):
        """Only items matching the specified genres are returned."""
        results = get_popular_by_genre(
            item_model=Book,
            genre_prefs={self.genre1: 5.0},
            limit=10,
        )
        result_items = {item for _, item in results}
        self.assertIn(self.book1, result_items)
        self.assertNotIn(self.book2, result_items)


class BoostNewItemsTests(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name="BoostGenre")
        self.user = CustomUser.objects.create_user(
            email="boostuser@example.com", password="password", first_name="Boost"
        )

        # Create a "new" book with no ratings
        self.new_book = Book.objects.create(
            title="New Unrated Book",
            author="Author New",
            isbn="boost-1",
            description="Desc",
            language="English",
            pages=300,
            likedPercent=70,
        )
        self.new_book.genre.add(self.genre)

        # Create an established book with many ratings
        self.established_book = Book.objects.create(
            title="Established Book",
            author="Author Est",
            isbn="boost-2",
            description="Desc",
            language="English",
            pages=250,
            likedPercent=90,
        )
        self.established_book.genre.add(self.genre)

        # Give the established book many ratings
        for i in range(10):
            u = CustomUser.objects.create_user(
                email=f"rater{i}@boost.com", password="password", first_name=f"Rater{i}"
            )
            UserBookRating.objects.create(user=u, book=self.established_book, rating=8)

    def test_new_item_boosted(self):
        """Item with 0 ratings but matching genre gets boosted score."""
        existing_recs = [(50.0, self.established_book)]
        boosted = boost_new_items(
            recommendations=existing_recs,
            interaction_model=UserBookRating,
            item_field="book",
            genre_prefs={self.genre: 5.0},
            item_model=Book,
            min_ratings=5,
        )
        # Should now include the new book
        boosted_pks = {item.pk for _, item in boosted}
        self.assertIn(self.new_book.pk, boosted_pks)

    def test_no_boost_without_genre_match(self):
        """Items not matching user's genres should not be boosted."""
        other_genre = Genre.objects.create(name="OtherBoostGenre")
        boosted = boost_new_items(
            recommendations=[],
            interaction_model=UserBookRating,
            item_field="book",
            genre_prefs={other_genre: 5.0},
            item_model=Book,
            min_ratings=5,
        )
        boosted_pks = {item.pk for _, item in boosted}
        self.assertNotIn(self.new_book.pk, boosted_pks)
