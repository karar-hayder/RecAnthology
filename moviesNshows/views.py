from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from .api.serializers import Genre,GenreSerializer,TvMedia,TvMediaSerializer
from django.db.models import Q
from myutils import ExtraTools
from rest_framework.permissions import IsAuthenticated,IsAdminUser


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

class CreateTvMedia(APIView):
    model = TvMedia
    serializer = TvMediaSerializer
    permission_classes = [IsAuthenticated,IsAdminUser]

    def post(self,request: Request):
        serializer = self.serializer(data=request.data)
        self.serializer.gens = request.data.get('genre')
        # print(request.POST)
        if serializer.is_valid():
            in_db = self.model.objects.filter(**serializer.validated_data)
            if in_db.exists():
                return Response({"data":self.serializer(in_db.first()).data},status=status.HTTP_200_OK)    
            new_data= serializer.save()
            return Response({'data':self.serializer(new_data).data},status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

class GetTvMedia(APIView):
    model = TvMedia
    serializer = TvMediaSerializer

    def get(self,request):
        id_query = self.request.GET.get('id')
        if not id_query:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        query = Q()  
        query &= Q(id__icontains=id_query)
        return Response({"data":self.serializer(self.model.objects.get(query)).data})
        