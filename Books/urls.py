from django.urls import path
from . import API_views
from . import views


from users.API_views import RateBook

urlpatterns = [
    #### Main ####
    path("", views.MainPage.as_view(), name="home"),
    path("books/explore/", views.ExploreBooksPage.as_view(), name="explore books"),

    #### API ####
    # path('', API_views.IndexView.as_view(), name='index'),
    path('api/books/genres/', API_views.AllGenres.as_view(), name='books-all-genres'),
    path('api/books/', API_views.AllBooks.as_view(), name='books-all'),
    path('api/books/<int:id_query>/', API_views.GetBook.as_view(), name='book-detail'),
    path('api/books/filter/', API_views.FilterBooks.as_view(), name='books-filter'),
    path('api/books/genre/create/', API_views.CreateGenre.as_view(), name='books-create-genre'),
    path('api/books/create/', API_views.CreateBook.as_view(), name='books-create'),
    path('api/books/recommend/public/', API_views.PublicRecommendBooks.as_view(), name='books-recommend-public'),
    path('api/books/recommend/private/', API_views.PrivateRecommendBooks.as_view(), name='books-recommend-private'),
    path('api/books/rate/', RateBook.as_view(), name='books-rate'),
]
