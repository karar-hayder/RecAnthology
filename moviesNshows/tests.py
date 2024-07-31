from django.test import TestCase
from .models import Genre, TvMedia
import uuid
# Create your tests here.

class GenreTestCase(TestCase):
    def setUp(self) -> None:
        self.genre = Genre.objects.create(name='Comedy')

    def test_genre_creation(self):
        ### Test that the genre is created correctly
        self.assertEqual(self.genre.name, 'Comedy')

    def test_genre_str_method(self):
        ### Test the __str__ method of the genre
        self.assertEqual(str(self.genre), 'Comedy')

    def test_genre_update(self):
        ### Test updating a genre's attributes
        self.genre.name = 'Drama'
        self.genre.save()
        updated_genre = Genre.objects.get(id=self.genre.id)
        self.assertEqual(updated_genre.name, 'Drama')

    def test_genre_delete(self):
        ### Test deleting a genre
        genre_id = self.genre.id
        self.genre.delete()
        with self.assertRaises(Genre.DoesNotExist):
            Genre.objects.get(id=genre_id)

class TvMediaTestCase(TestCase):
    def setUp(self) -> None:
        self.genre1 = Genre.objects.create(name='Action')
        self.genre2 = Genre.objects.create(name='Thriller')

        self.tv_media = TvMedia.objects.create(
            media_type='Movie',
            original_title='Inception',
            primary_title='Inception',
            over18=False,
            startyear=2010,
            length=148,
        )
        self.tv_media.genre.set([self.genre1, self.genre2])

    def test_tv_media_creation(self):
        ### Test that the TvMedia is created correctly
        self.assertEqual(self.tv_media.media_type, 'Movie')
        self.assertEqual(self.tv_media.original_title, 'Inception')
        self.assertEqual(self.tv_media.primary_title, 'Inception')
        self.assertEqual(self.tv_media.over18, False)
        self.assertEqual(self.tv_media.startyear, 2010)
        self.assertEqual(self.tv_media.length, 148)

    def test_tv_media_genres(self):
        ### Test that the TvMedia has the correct genres
        genres = self.tv_media.genre.all()
        self.assertEqual(genres.count(), 2)
        self.assertIn(self.genre1, genres)
        self.assertIn(self.genre2, genres)

    def test_tv_media_str_method(self):
        ### Test the __str__ method of the TvMedia
        expected_str = f'Inception:148:2010 -- {self.tv_media.id}'
        self.assertEqual(str(self.tv_media), expected_str)

    def test_tv_media_update(self):
        ### Test updating a TvMedia's attributes
        self.tv_media.original_title = 'Interstellar'
        self.tv_media.save()
        updated_tv_media = TvMedia.objects.get(id=self.tv_media.id)
        self.assertEqual(updated_tv_media.original_title, 'Interstellar')

    def test_tv_media_delete(self):
        ### Test deleting a TvMedia
        tv_media_id = self.tv_media.id
        self.tv_media.delete()
        with self.assertRaises(TvMedia.DoesNotExist):
            TvMedia.objects.get(id=tv_media_id)