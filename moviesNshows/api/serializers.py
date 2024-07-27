from rest_framework import serializers
from ..models import TvMedia, Genre

# serializers.
class GenreSerializer(serializers.Serializer):
    # id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()

    class Meta:
        model = Genre
        fields = ['name']

    def create(self, validated_data):
        return Genre.objects.get_or_create(name=validated_data['name'])

class TvMediaSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    media_type = serializers.CharField()
    original_title = serializers.CharField()
    primary_title = serializers.CharField(allow_null=True)
    over18 = serializers.IntegerField()
    startyear = serializers.IntegerField(allow_null=True)
    length = serializers.IntegerField()
    genre = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
        many=True
    )
    def create(self, validated_data):
        genres_data = self.gens
        tvmedia = TvMedia.objects.create(**validated_data)
        for genre_data in genres_data:            
            tvmedia.genre.add(Genre.objects.get_or_create(name=genre_data)[0])
        return tvmedia
    
    def validate(self, attrs):
        return super().validate(attrs)
    class Meta:
        model = TvMedia
        fields = '__all__'
        depth = 1