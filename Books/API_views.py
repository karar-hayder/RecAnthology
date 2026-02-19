from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from myutils.api_mixins import BaseCRUDMixin, RecommendationMixin
from myutils.ExtraTools import get_cached_or_queryset
from RecAnthology.custom_throttles import AdminThrottle

from .serializers import Book, BookSerializer, Genre, GenreSerializer


class IndexView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        return Response("OK")


class AllGenres(BaseCRUDMixin, APIView):
    permission_classes = [AllowAny]
    model = Genre
    serializer = GenreSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        return self.handle_list("books_genres")


class CreateGenre(BaseCRUDMixin, APIView):
    model = Genre
    serializer = GenreSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    throttle_classes = [AdminThrottle]

    def post(self, request):
        return self.handle_create(request)


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


class PublicRecommendBooks(RecommendationMixin, APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    model = Book
    serializer = BookSerializer
    item_type_key = "book"
    allowed_types = ("books",)

    def post(self, request):
        return self.handle_public_recommendation(request, Genre)


class PrivateRecommendBooks(RecommendationMixin, APIView):
    throttle_classes = [UserRateThrottle]
    model = Book
    serializer = BookSerializer
    permission_classes = [IsAuthenticated]
    item_type_key = "book"
    allowed_types = ("books",)

    def get(self, request):
        from users.models import UserBookRating

        return self.handle_private_recommendation(
            request=request,
            genre_prefs_fn=request.user.get_books_genre_preferences,
            interaction_model=UserBookRating,
            item_field="book",
            cache_key=f"{request.user.pk}_book_recommendation",
        )
