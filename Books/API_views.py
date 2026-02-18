from django.core.cache import cache
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from myutils import ExtraTools, recommendation
from myutils.ExtraTools import get_cached_or_queryset
from RecAnthology.custom_throttles import AdminThrottle

from .serializers import Book, BookSerializer, Genre, GenreSerializer


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
        rated = request.GET.get(
            "rated"
        )  # expects "true" or "false" (case-insensitive string)

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

        base_qs = (
            self.model.objects.filter(query).order_by("-likedPercent")
            if query
            else self.model.objects.order_by("-likedPercent")[:50]
        )

        # Filter for rated and unrated books for the authenticated user
        user = request.user if request.user.is_authenticated else None
        if rated is not None and user is not None:
            rated_bool = rated.lower() == "true"
            # Import inside to avoid potential circular import
            from users.models import UserBookRating

            rated_books_qs = UserBookRating.objects.filter(user=user).values_list(
                "book_id", flat=True
            )
            if rated_bool:
                base_qs = base_qs.filter(id__in=rated_books_qs)
            else:
                base_qs = base_qs.exclude(id__in=rated_books_qs)

        serialized = self.serializer(base_qs, many=True).data
        return Response({"data": serialized})


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

        suggestions = recommendation.get_content_based_recommendations(
            user_needed_genres=genre_objs,
            max_genres=max_genres,
            max_media_per_genre=max_books,
            scoring_fn=None,
            relativity_decimals=1,
            default_preference_score=6,
        )

        sorted_suggestions = sorted(suggestions, key=lambda tup: tup[0], reverse=True)
        final_media = [m for _, m in sorted_suggestions][:100]
        relativity_list = [s[0] for s in sorted_suggestions][:100]

        books_data = BookSerializer(final_media, many=True).data
        response_data = {}
        for idx, (rel, book_entry) in enumerate(zip(relativity_list, books_data)):
            response_data[str(idx)] = {"relativity": rel, "book": book_entry}

        return Response({"length": len(final_media), "data": response_data})


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

        needed_genres = request.user.get_books_genre_preferences()
        use_cf = request.GET.get("cf", "true").lower() == "true"

        if not needed_genres:
            books = self.model.objects.order_by("-likedPercent")
            books_data = self.serializer(books, many=True).data
            return Response({"length": books.count(), "data": books_data})

        if use_cf:
            from users.models import UserBookRating

            hybrid_results = recommendation.get_hybrid_recommendation(
                user=request.user,
                user_needed_genres=needed_genres,
                interaction_model=UserBookRating,
                item_model=self.model,
                item_field="book",
                top_n=100,
            )
            final_media = [item for _, item in hybrid_results]
            relativity_list = [score for score, _ in hybrid_results]
        else:
            max_genres = 10
            max_books = 21
            suggestions = recommendation.get_content_based_recommendations(
                user_needed_genres=needed_genres,
                max_num_genres=max_genres,
                max_media_per_genre=max_books,
                scoring_fn=None,
                relativity_decimals=1,
                default_preference_score=6,
                allowed_types=("books",),
            )
            sorted_suggestion = sorted(
                suggestions, key=lambda tup: tup[0], reverse=True
            )
            final_media = [b for _, b in sorted_suggestion][:100]
            relativity_list = [s[0] for s in sorted_suggestion][:100]

        books_data = BookSerializer(final_media, many=True).data
        response_data = {}
        for idx, (rel, book_entry) in enumerate(zip(relativity_list, books_data)):
            response_data[str(idx)] = {"relativity": rel, "book": book_entry}

        cache.set(cache_key, response_data, 60 * 60)
        return Response({"length": len(response_data), "data": response_data})
