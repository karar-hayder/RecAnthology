from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from .api.serializers import BookSerializer,Book, GenreSerializer, Genre
from django.db.models import Q
from . import ExtraTools
from rest_framework.permissions import IsAuthenticated,IsAdminUser

class IndexView(APIView):
    def get(self,request):
        return Response("OK")
    
class AllGenres(APIView):
    model = Genre
    serializer = GenreSerializer

    def get(self,request):
        data = {"data":self.serializer(self.model.objects.all(),many=True).data}

        return Response(data)
    
class CreateGenre(APIView):
    model = Genre
    serializer = GenreSerializer
    permission_classes = [IsAuthenticated,IsAdminUser]

    def post(self,request):
        serializer = self.serializer(data=request.data)
        if serializer.is_valid():
            in_db = self.model.objects.filter(**serializer.validated_data)
            if in_db.exists():
                return Response({"data":self.serializer(in_db.first()).data},status=status.HTTP_200_OK)    
            new_data= serializer.save()
            return Response({'data':self.serializer(new_data).data},status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class AllBooks(APIView):
    model = Book
    serializer = BookSerializer

    def get(self,request):
        data = {"data":self.serializer(self.model.objects.all().order_by("-likedPercent")[:50],many=True).data}

        return Response(data)
    
class CreateBook(APIView):
    model = Book
    serializer = BookSerializer
    permission_classes = [IsAuthenticated,IsAdminUser]

    def post(self,request: Request):
        serializer = self.serializer(data=request.data)
        self.serializer.gens = request.data.getlist('genre')
        # print(request.POST)
        if serializer.is_valid():
            in_db = self.model.objects.filter(**serializer.validated_data)
            if in_db.exists():
                return Response({"data":self.serializer(in_db.first()).data},status=status.HTTP_200_OK)    
            new_data= serializer.save()
            return Response({'data':self.serializer(new_data).data},status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
    
class GetBook(APIView):
    model = Book
    serializer = BookSerializer

    def get(self,request):
        id_query = self.request.GET.get('id')
        if not id_query:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        query = Q()  
        if id_query:
            query &= Q(id__icontains=id_query)
        if query:
            return Response({"data":self.serializer(self.model.objects.get(query)).data})
        

class FilterBooks(APIView):
    model = Book
    serializer = BookSerializer

    def get(self,request):
        title_query = self.request.GET.get('title')
        id_query = self.request.GET.get('id')
        author_query = self.request.GET.get('author')
        # isbn_query = self.request.GET.get('isbn') ### maybe Remove later
        # language_query = self.request.GET.get('language')
        query = Q()

        if title_query:
            query &= Q(title__icontains=title_query)
        if id_query:
            query &= Q(id__icontains=id_query)
        if author_query:
            query &= Q(author__icontains=author_query)
        # if isbn_query:
        #     query &= Q(isbn__icontains=isbn_query)
        # if language_query:
        #     query &= Q(language__icontains=language_query)

        if query:
            data = self.model.objects.filter(query).order_by("-likedPercent")
            return Response({"data":self.serializer(data,many=len(data) > 1).data})
        else:
            return Response({"data":self.serializer(self.model.objects.order_by("-likedPercent")[:50],many=True).data})

class PublicRecommendBooks(APIView):
    def post(self,request):
        needed = request.data
        try:
            needed = {Genre.objects.get(name=key):i for key,i in needed.items()}
        except Exception as e:
            return Response(f"{e}",status=status.HTTP_406_NOT_ACCEPTABLE)
        needed_gens = ExtraTools.quickSort([(j,i) for i, j in needed.items()])[::-1]
        highest_num = max(needed.values())
        suggestion = []
        books = []
        if len(needed_gens) > 5:
            needed_gens = needed_gens[:5]
        for rating ,gener in needed_gens:
            for ind,book in enumerate(gener.books.all()):
                if ind > 5:
                    break
                elif book in books:
                    continue

                rt = 0
                for g in book.genre.all():
                    if g not in needed:
                        needed[g] = 0
                    rt += needed[g]

                suggestion.append((round(rt/highest_num,3),book))
                books.append(book)
        
        sort = ExtraTools.quickSort(suggestion)[::-1]
        final_sort = [j for i,j in sort]
        if len(final_sort) > 100:final_sort=final_sort[:100]
        data = {}
        for ind, book in enumerate(BookSerializer(final_sort,many=len(sort) > 1).data):
            data[str(ind)] = {"relativity":sort[ind][0],"book":book}

        return Response({"length" : len(final_sort),"data":data})

class PrivateRecommendBooks(APIView):
    model = Book
    serializer = BookSerializer
    permission_classes = [IsAuthenticated]

    def get(self,request):
        needed : dict = self.request.user.get_genre_preferences()
        if len(needed.keys()) < 1:
            books = self.model.objects.order_by('-likedPercent')
            data = self.serializer(books,many=len(sort) > 1).data
            return Response({"length" : books.count(),"data":data})

        needed_gens = ExtraTools.quickSort([(j,i) for i, j in needed.items()])[::-1]
        highest_num = max(needed.values())
        suggestion = []
        books = []
        if len(needed_gens) > 10:
            needed_gens = needed_gens[:10]
        for rating ,gener in needed_gens:
            for ind,book in enumerate(gener.books.all()):
                if ind > 20:
                    break
                elif book in books:
                    continue

                rt = 0
                for g in book.genre.all():
                    if g not in needed:
                        needed[g] = 0
                    rt += needed[g] * 10

                suggestion.append((round(rt/highest_num,2),book))
                books.append(book)
        
        sort = ExtraTools.quickSort(suggestion)[::-1]
        final_sort = [j for i,j in sort]
        if len(final_sort) > 100:final_sort=final_sort[:100]
        data = {}
        for ind, book in enumerate(BookSerializer(final_sort,many=len(sort) > 1).data):
            data[str(ind)] = {"relativity":sort[ind][0],"book":book}

        return Response({"length" : len(final_sort),"data":data})