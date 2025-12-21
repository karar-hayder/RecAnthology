from django.core.cache import cache
from django.db.models import Count
from django.views.generic import TemplateView

from .models import Book, Genre


class MainPage(TemplateView):
    template_name = "home.html"


class ExploreBooksPage(TemplateView):
    template_name = "books/explore_books.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        most_liked_books = cache.get("most_liked_books", None)
        recently_added_books = cache.get("recently_added_books", None)
        genres_books = cache.get("genre_books", None)

        if not genres_books:
            recently_added_books = Book.objects.order_by("-pk")[:10]
            most_liked_books = Book.objects.order_by("-likedPercent")[:10]
            genres = Genre.objects.annotate(books_count=Count("books")).order_by(
                "-books_count"
            )[:10]

            books = Book.objects.filter(genre__in=genres).distinct()
            genres_books = {}
            for genre in genres:
                genre_books = books.filter(genre=genre)[:10]
                genres_books[genre] = genre_books

            cache.set("recently_added_books", recently_added_books, 60 * 60)
            cache.set("most_liked_books", most_liked_books, 60 * 60)
            cache.set("genre_books", genres_books, 60 * 60)

        context["recently_added_books"] = recently_added_books
        context["most_liked_books"] = most_liked_books
        context["genre_books"] = genres_books

        return context
