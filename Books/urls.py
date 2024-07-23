from django.urls import path
from .views import (IndexView
                    ,AllGenres
                    ,AllBooks
                    ,FilterBooks
                    ,GetBook
                    ,CreateBook
                    ,CreateGenre
                    ,PublicRecommendBooks
                    ,PrivateRecommendBooks)
from users.views import RateBook

urlpatterns = [
    path('',IndexView.as_view()),
    path('api/genres/all/',AllGenres.as_view()),
    path('api/filter/',FilterBooks.as_view()),
    path('api/get/',GetBook.as_view()),
    path('api/create/genre/',CreateGenre.as_view()),
    path('api/create/book/',CreateBook.as_view()),
    path('api/allbooks/',AllBooks.as_view()),
    path('api/recommend/public/',PublicRecommendBooks.as_view()),
    path('api/recommend/private/',PrivateRecommendBooks.as_view()),
    path('api/rate/book/',RateBook.as_view()),
]