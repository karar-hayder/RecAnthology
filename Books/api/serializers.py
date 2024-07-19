from rest_framework import serializers
from ..models import Book, Genere

# serializers.
class GenereSerializer(serializers.Serializer):
    # id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()

    class Meta:
        model = Genere
        fields = ['name']

    def create(self, validated_data):
        return Genere.objects.get_or_create(name=validated_data['name'])

class BookSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(required=True, max_length=300)
    author = serializers.CharField(max_length=300)
    # genere = GenereSerializer(many=True)
    genere = serializers.SlugRelatedField(
        slug_field='name',
        read_only=True,
        many=True
    )
    isbn = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=3000)
    language = serializers.CharField(max_length=50)
    edition = serializers.CharField(max_length=500)
    pages = serializers.IntegerField()
    likedPercent = serializers.IntegerField()

    def create(self, validated_data):
        generes_data = self.gens

        book = Book.objects.create(**validated_data)
        # print('i got to genere creation --------------------------------------')
        for genere_data in generes_data:            
            book.genere.add(Genere.objects.get_or_create(name=genere_data)[0])
        return book
    
    def validate(self, attrs):
        # print("VAL ",attrs)
        return super().validate(attrs)
    class Meta:
        model = Book
        fields = '__all__'
        depth = 1