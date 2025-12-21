from django.test import TestCase

from .models import Book, Genre

# Create your tests here.


class GenreTestCase(TestCase):
    def setUp(self) -> None:
        self.genre = Genre.objects.create(name="Comedy")

    def test_genre_creation(self):
        ### Test that the genre is created correctly
        self.assertEqual(self.genre.name, "Comedy")

    def test_genre_str_method(self):
        ### Test the __str__ method of the genre
        self.assertEqual(str(self.genre), "Comedy")

    def test_genre_update(self):
        ### Test updating a genre's attributes
        self.genre.name = "Drama"
        self.genre.save()
        updated_genre = Genre.objects.get(id=self.genre.id)
        self.assertEqual(updated_genre.name, "Drama")

    def test_genre_delete(self):
        ### Test deleting a genre
        genre_id = self.genre.id
        self.genre.delete()
        with self.assertRaises(Genre.DoesNotExist):
            Genre.objects.get(id=genre_id)


class BookTestCase(TestCase):
    def setUp(self) -> None:
        # Creating genres for the test book
        self.genre1 = Genre.objects.create(name="Fiction")
        self.genre2 = Genre.objects.create(name="Adventure")
        self.genre3 = Genre.objects.create(name="Mystery")

        self.book = Book.objects.create(
            title="Test Testing",
            author="Karar",
            isbn="-111",
            description="Test",
            language="English",
            edition="First",
            pages=100,
            likedPercent=90,
        )
        self.book.genre.set([self.genre1, self.genre2, self.genre3])

    def test_book_creation(self):
        ### Test that the book is created correctly
        self.assertEqual(self.book.title, "Test Testing")
        self.assertEqual(self.book.author, "Karar")
        self.assertEqual(self.book.isbn, "-111")
        self.assertEqual(self.book.description, "Test")
        self.assertEqual(self.book.language, "English")
        self.assertEqual(self.book.edition, "First")
        self.assertEqual(self.book.pages, 100)
        self.assertEqual(self.book.likedPercent, 90)

    def test_book_genres(self):
        ### Test that the book has the correct genres
        genres = self.book.genre.all()
        self.assertEqual(genres.count(), 3)
        self.assertIn(self.genre1, genres)
        self.assertIn(self.genre2, genres)
        self.assertIn(self.genre3, genres)

    def test_str_method(self):
        ### Test the __str__ method of the book
        self.assertEqual(str(self.book), f"Test Testing:-111:First -- {self.book.id}")

    def test_book_update(self):
        ### Test updating a book's attributes
        self.book.title = "Updated Title"
        self.book.save()
        updated_book = Book.objects.get(id=self.book.id)
        self.assertEqual(updated_book.title, "Updated Title")

    def test_book_delete(self):
        ### Test deleting a book
        book_id = self.book.id
        self.book.delete()
        with self.assertRaises(Book.DoesNotExist):
            Book.objects.get(id=book_id)
