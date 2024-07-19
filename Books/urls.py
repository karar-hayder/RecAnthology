from django.urls import path
from .views import (IndexView
                    ,AllGeneres
                    ,AllBooks
                    ,FilterBooks
                    ,GetBook
                    ,CreateBook
                    ,CreateGenere)

urlpatterns = [
    path('',IndexView.as_view()),
    path('api/generes/all/',AllGeneres.as_view()),
    path('api/filter/',FilterBooks.as_view()),
    path('api/get/',GetBook.as_view()),
    path('api/create/genere/',CreateGenere.as_view()),
    path('api/create/book/',CreateBook.as_view()),
    path('api/allbooks/',AllBooks.as_view()),
]