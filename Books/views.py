from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from .api.serializers import BookSerializer,Book, GenereSerializer, Genere
from django.db.models import Q

class IndexView(APIView):
    def get(self,request):
        return Response("OK")
    
class AllGeneres(APIView):
    model = Genere
    serializer = GenereSerializer

    def get(self,request):
        data = {"data":self.serializer(self.model.objects.all(),many=True).data}

        return Response(data)
    
class CreateGenere(APIView):
    model = Genere
    serializer = GenereSerializer

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
        data = {"data":self.serializer(self.model.objects.all(),many=True).data}

        return Response(data)
    
class CreateBook(APIView):
    model = Book
    serializer = BookSerializer

    def post(self,request: Request):
        serializer = self.serializer(data=request.data)
        self.serializer.gens = request.data.getlist('genere')
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
        isbn_query = self.request.GET.get('isbn')
        language_query = self.request.GET.get('language')
        query = Q()

        if title_query:
            query &= Q(title__icontains=title_query)
        if id_query:
            query &= Q(id__icontains=id_query)
        if author_query:
            query &= Q(author__icontains=author_query)
        if isbn_query:
            query &= Q(isbn__icontains=isbn_query)
        if language_query:
            query &= Q(language__icontains=language_query)

        if query:
            data = self.model.objects.filter(query).order_by("-likedPercent")
            return Response({"data":self.serializer(data,many=len(data) > 1).data})
        else:
            return Response({"data":self.serializer(self.model.objects.order_by("-likedPercent")[:50],many=True).data})
