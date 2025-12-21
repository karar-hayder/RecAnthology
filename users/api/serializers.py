from rest_framework import serializers

from Books.api.serializers import BookSerializer
from moviesNshows.api.serializers import TvMediaSerializer

from ..models import (  # BookGenre,; TvGenre,; UserBooksGenrePreference,; UserTvMediaGenrePreference,
    Book,
    CustomUser,
    TvMedia,
    UserBookRating,
    UserTvMediaRating,
)


class UserSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(max_length=50)

    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "refreshToken", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        print(attrs)
        return super().validate(attrs)

    def create(self, validated_data):
        if not CustomUser.objects.filter(email=validated_data["email"]).exists():
            user = CustomUser.objects.create_user(**validated_data)
            user.set_password(validated_data["password"])
            user.save()
            return user
        else:
            return False


class BookRatingSerializer(serializers.Serializer):
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    book_details = BookSerializer(source="book", read_only=True)
    rating = serializers.IntegerField(min_value=1, max_value=10)

    class Meta:
        model = UserBookRating
        fields = ["__all__"]
        depth = 1

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else None
        book = validated_data.get("book")
        rating = validated_data.get("rating")

        user_book_rating, created = UserBookRating.objects.update_or_create(
            user=user, book=book, defaults={"rating": rating}
        )
        return user_book_rating


class TvMediaRatingSerializer(serializers.Serializer):
    tvmedia = serializers.PrimaryKeyRelatedField(queryset=TvMedia.objects.all())
    tvmedia_details = TvMediaSerializer(source="tvmedia", read_only=True)
    rating = serializers.IntegerField(min_value=1, max_value=10)

    class Meta:
        model = UserTvMediaRating
        fields = ["__all__"]
        depth = 1

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else None
        tvmedia = validated_data.get("tvmedia")
        rating = validated_data.get("rating")

        user_media_rating, created = UserTvMediaRating.objects.update_or_create(
            user=user, tvmedia=tvmedia, defaults={"rating": rating}
        )
        return user_media_rating
