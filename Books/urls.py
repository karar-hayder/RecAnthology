from django.urls import path
from .views import (
    IndexView,
    AllGenres,
    AllBooks,
    FilterBooks,
    GetBook,
    CreateBook,
    CreateGenre,
    PublicRecommendBooks,
    PrivateRecommendBooks
)
from users.views import RateBook

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('api/books/genres/', AllGenres.as_view(), name='books-all-genres'),
    path('api/books/', AllBooks.as_view(), name='books-all'),
    path('api/books/<int:id_query>/', GetBook.as_view(), name='book-detail'),
    path('api/books/filter/', FilterBooks.as_view(), name='books-filter'),
    path('api/books/genre/create/', CreateGenre.as_view(), name='books-create-genre'),
    path('api/books/create/', CreateBook.as_view(), name='books-create'),
    path('api/books/recommend/public/', PublicRecommendBooks.as_view(), name='books-recommend-public'),
    path('api/books/recommend/private/', PrivateRecommendBooks.as_view(), name='books-recommend-private'),
    path('api/books/rate/', RateBook.as_view(), name='books-rate'),
]
