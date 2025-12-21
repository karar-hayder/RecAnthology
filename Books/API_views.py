from django.core.cache import cache
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from myutils import ExtraTools
from myutils.ExtraTools import get_cached_or_queryset
from RecAnthology.custom_throttles import AdminThrottle

from .api.serializers import Book, BookSerializer, Genre, GenreSerializer


class IndexView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        return Response("OK")


class AllGenres(APIView):
    permission_classes = [AllowAny]
    model = Genre
    serializer = GenreSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        data = get_cached_or_queryset(
            "books_genres", self.model.objects.all(), self.serializer, many=True
        )
        return Response({"data": data})


class CreateGenre(APIView):
    model = Genre
    serializer = GenreSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    throttle_classes = [AdminThrottle]

    def post(self, request):
        serializer = self.serializer(data=request.data)
        if serializer.is_valid():
            in_db = self.model.objects.filter(**serializer.validated_data)
            if in_db.exists():
                return Response(
                    {"data": self.serializer(in_db.first()).data},
                    status=status.HTTP_200_OK,
                )
            new_genre = serializer.save()
            return Response(
                {"data": self.serializer(new_genre).data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AllBooks(APIView):
    model = Book
    serializer = BookSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        data = get_cached_or_queryset(
            "all_books",
            self.model.objects.all().order_by("-likedPercent")[:50],
            self.serializer,
            many=True,
        )
        return Response({"data": data})


class CreateBook(APIView):
    model = Book
    serializer = BookSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    throttle_classes = [AdminThrottle]

    def post(self, request: Request):
        serializer = self.serializer(data=request.data)
        if hasattr(self.serializer, "gens"):
            self.serializer.gens = request.data.getlist("genre")
        if serializer.is_valid():
            in_db = self.model.objects.filter(**serializer.validated_data)
            if in_db.exists():
                return Response(
                    {"data": self.serializer(in_db.first()).data},
                    status=status.HTTP_200_OK,
                )
            new_book = serializer.save()
            return Response(
                {"data": self.serializer(new_book).data}, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetBook(APIView):
    model = Book
    serializer = BookSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, id_query):
        if not id_query:
            return Response(
                {"error": "Book id is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            book = self.model.objects.get(id=id_query)
        except self.model.DoesNotExist:
            return Response(
                {"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response({"data": self.serializer(book).data})


class FilterBooks(APIView):
    model = Book
    serializer = BookSerializer
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        filters = {}
        title = request.GET.get("title")
        book_id = request.GET.get("id")
        author = request.GET.get("author")
        genre = request.GET.get("genre")
        liked_percent = request.GET.get("likedPercent")

        query = Q()
        if title:
            query &= Q(title__icontains=title)
        if book_id:
            query &= Q(id__icontains=book_id)
        if author:
            query &= Q(author__icontains=author)
        if genre:
            query &= Q(genre__name__icontains=genre)
        if liked_percent:
            try:
                liked_value = int(liked_percent)
                query &= Q(likedPercent__gte=liked_value)
            except (ValueError, TypeError):
                return Response(
                    {"error": "likedPercent must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        qs = (
            self.model.objects.filter(query).order_by("-likedPercent")
            if query
            else self.model.objects.order_by("-likedPercent")[:50]
        )
        serialized = self.serializer(qs, many=True).data
        return Response({"data": serialized})


def _build_recommendation(
    needed,
    max_genres,
    max_books_per_genre,
    scale_func,
    relativity_round=3,
    default_needed=0,
):
    """Core logic reused by both Public and Private recommend endpoints."""
    # Sort (value, key) by value descending, keep top genres
    needed_gens = ExtraTools.quickSort([(v, k) for k, v in needed.items()])[::-1][
        :max_genres
    ]
    books_seen = set()
    suggestions = []

    for rating, genre in needed_gens:
        related_books = genre.books.all().prefetch_related("genre")[
            :max_books_per_genre
        ]
        for book in related_books:
            if book.pk in books_seen:
                continue
            rt_score = 0
            book_genres = list(book.genre.all())
            for g in book_genres:
                needed_value = needed.get(g, default_needed)
                rt_score += scale_func(needed_value)

            score = (
                round(rt_score / (len(book_genres) * 100), relativity_round)
                if book_genres
                else 0
            )
            suggestions.append((score, book))
            books_seen.add(book.pk)
    return suggestions


class PublicRecommendBooks(APIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes = [AllowAny]

    def post(self, request):
        # Validate request body is a dict of {genre:score}
        needed = request.data
        if not isinstance(needed, dict):
            return Response(
                {"error": "Request must be a dictionary of {genre: value}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            genre_objs = {
                Genre.objects.get(name=key): value for key, value in needed.items()
            }
        except Genre.DoesNotExist as e:
            return Response(
                {"error": f"Genre not found: {e}"},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_406_NOT_ACCEPTABLE)

        max_genres = 5
        max_books = 6  # per genre

        def scale_func(val):
            # Emulating the old scale: scale val from (1,10) to (-5,5) and *20
            return ExtraTools.scale(val, (1, 10), (-5, 5)) * 20

        suggestion = _build_recommendation(
            genre_objs,
            max_genres=max_genres,
            max_books_per_genre=max_books,
            scale_func=scale_func,
            relativity_round=1,
            default_needed=6,
        )

        # Sort suggestions by score descending, unique per book
        sorted_suggestion = sorted(suggestion, key=lambda tup: tup[0], reverse=True)
        final_books = [b for _, b in sorted_suggestion][:100]
        relativity_list = [s[0] for s in sorted_suggestion][:100]

        books_data = BookSerializer(final_books, many=True).data
        response_data = {}
        for idx, (rel, book_entry) in enumerate(zip(relativity_list, books_data)):
            response_data[str(idx)] = {"relativity": rel, "book": book_entry}

        return Response({"length": len(final_books), "data": response_data})


class PrivateRecommendBooks(APIView):
    throttle_classes = [UserRateThrottle]
    model = Book
    serializer = BookSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cache_key = f"{request.user.pk}_book_recommendation"
        data = cache.get(cache_key)
        if data:
            return Response({"length": len(data), "data": data})

        needed = request.user.get_books_genre_preferences()
        if not needed:
            books = self.model.objects.order_by("-likedPercent")
            books_data = self.serializer(books, many=True).data
            return Response({"length": books.count(), "data": books_data})

        max_genres = 10
        max_books = 21  # allow up to 21 books per genre for private

        def scale_func(val):
            return val * 20

        suggestion = _build_recommendation(
            needed,
            max_genres=max_genres,
            max_books_per_genre=max_books,
            scale_func=scale_func,
            relativity_round=3,
            default_needed=0,
        )

        # Sort suggestions, take up to 100
        sorted_suggestion = sorted(suggestion, key=lambda tup: tup[0], reverse=True)
        final_books = [b for _, b in sorted_suggestion][:100]
        relativity_list = [s[0] for s in sorted_suggestion][:100]

        books_data = BookSerializer(final_books, many=True).data
        response_data = {}
        for idx, (rel, book_entry) in enumerate(zip(relativity_list, books_data)):
            response_data[str(idx)] = {"relativity": rel, "book": book_entry}

        cache.set(cache_key, response_data, 60 * 60)
        return Response({"length": len(response_data), "data": response_data})
