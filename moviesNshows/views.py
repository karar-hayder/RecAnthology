from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from .api.serializers import Genre,GenreSerializer,TvMedia,TvMediaSerializer
from django.db.models import Q
from myutils import ExtraTools
from rest_framework.permissions import IsAuthenticated,IsAdminUser,AllowAny
from django.core.cache import cache
from rest_framework.throttling import UserRateThrottle,AnonRateThrottle
from RecAnthology.custom_throttles import AdminThrottle
class AllGenres(APIView):
    throttle_classes = [AnonRateThrottle,UserRateThrottle]
    permission_classes = [AllowAny]
    model = Genre
    serializer = GenreSerializer

    def get(self,request):
        data = cache.get("tvmedia_genres")
        if not data:
            data = self.serializer(self.model.objects.all(),many=True).data
            cache.set('tvmedia_genres',data,60*60)
        data = {"data":data}

        return Response(data)

class CreateGenre(APIView):
    model = Genre
    serializer = GenreSerializer
    permission_classes = [IsAuthenticated,IsAdminUser]
    throttle_classes = [AdminThrottle]

    def post(self,request):
        serializer = self.serializer(data=request.data)
        if serializer.is_valid():
            in_db = self.model.objects.filter(**serializer.validated_data)
            if in_db.exists():
                return Response({"data":self.serializer(in_db.first()).data},status=status.HTTP_200_OK)    
            new_data= serializer.save()
            return Response({'data':self.serializer(new_data).data},status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)


class AllTvMedia(APIView):
    throttle_classes = [AnonRateThrottle,UserRateThrottle]
    permission_classes = [AllowAny]
    model = TvMedia
    serializer = TvMediaSerializer
    def get(self,request):
        data = cache.get('all_tvmedia')
        if not data:
            data = self.model.objects.all().order_by("-startyear")[:50]
            data = {"data":self.serializer(data,many=True).data}
            cache.set('all_tvmedia',data,60*60)
        return Response(data)
class CreateTvMedia(APIView):
    model = TvMedia
    serializer = TvMediaSerializer
    permission_classes = [IsAuthenticated,IsAdminUser]
    throttle_classes = [AdminThrottle]

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
    throttle_classes = [AnonRateThrottle,UserRateThrottle]
    permission_classes = [AllowAny]
    model = TvMedia
    serializer = TvMediaSerializer

    def get(self,request,id_query):
        query = Q()  
        query &= Q(id__icontains=id_query)
        return Response({"data":self.serializer(self.model.objects.get(query)).data})
        
class FilterTvMedia(APIView):
    throttle_classes = [AnonRateThrottle,UserRateThrottle]
    model = TvMedia
    serializer = TvMediaSerializer
    permission_classes = [AllowAny]

    def get(self,request):
        title_query = self.request.GET.get('title')
        startyear_query = self.request.GET.get('start_year')
        endyear_query = self.request.GET.get('end_year')
        media_type_query = self.request.GET.get('media_type')
        genre_query = self.request.GET.get('genre')
        query = Q()

        if title_query:
            query &= Q(original_title__icontains=title_query)
        if media_type_query:
            query &= Q(media_type__icontains=media_type_query)
        if genre_query:
            query &= Q(genre__name__icontains=genre_query)
        if startyear_query:
            query &= Q(startyear__gte=int(startyear_query))
        if endyear_query:
            query &= Q(startyear__lte=int(endyear_query))
        

        if query:
            data = self.model.objects.filter(query).order_by("-startyear")
            return Response({"data":self.serializer(data,many=len(data) > 1).data})
        else:
            return Response({"data":self.serializer(self.model.objects.order_by("-startyear")[:50],many=True).data})
        
class PublicRecommendTvMedia(APIView):
    throttle_classes = [AnonRateThrottle,UserRateThrottle]
    permission_classes = [AllowAny]
    def post(self,request):
        needed = request.data
        try:
            needed : dict[Genre,int] = {Genre.objects.get(name=key):i for key,i in needed.items()}
        except Exception as e:
            return Response(f"{e}",status=status.HTTP_406_NOT_ACCEPTABLE)
        needed_gens = ExtraTools.quickSort([(j,i) for i, j in needed.items()])[::-1]
        highest_num = max(needed.values())
        suggestion = []
        tv_media = []
        if len(needed_gens) > 5:
            needed_gens = needed_gens[:5]
        for rating ,gener in needed_gens:
            for ind,media in enumerate(gener.tvmedia.all()):
                if ind > 5:
                    break
                elif media in tv_media:
                    continue

                rt = 0
                genres = media.genre.all()
                for g in genres:
                    if g not in needed:
                        needed[g] = 6
                    rt += ExtraTools.scale(needed[g],(1,10),(-5,5)) * 20

                suggestion.append((round(rt/(len(genres)),2),media))
                tv_media.append(media)
        
        sort = ExtraTools.quickSort(suggestion)[::-1]
        final_sort = [j for i,j in sort]
        if len(final_sort) > 100:final_sort=final_sort[:100]
        data = {}
        for ind, media in enumerate(TvMediaSerializer(final_sort,many=len(sort) > 1).data):
            data[str(ind)] = {"relativity":sort[ind][0],"media":media}

        return Response({"length" : len(final_sort),"data":data})

class PrivateRecommendTvMedia(APIView):
    throttle_classes = [UserRateThrottle]
    model = TvMedia
    serializer = TvMediaSerializer
    permission_classes = [IsAuthenticated]

    def get(self,request):

        cache_key = f"{self.request.user.pk}_books_recommendation"
        data = cache.get(cache_key)
        if not data:
            needed : dict = self.request.user.get_media_genre_preferences()
            if len(needed.keys()) < 1:
                tv_media = self.model.objects.order_by('-startyear')[:100]
                data = self.serializer(tv_media,many=len(tv_media) > 1).data
                return Response({"length" : tv_media.count(),"data":data})

            needed_gens = ExtraTools.quickSort([(j,i) for i, j in needed.items()])[::-1]
            highest_num = max(needed.values()) * 20
            suggestion = []
            tv_media = []
            if len(needed_gens) > 10:
                needed_gens = needed_gens[:10]
            for rating ,gener in needed_gens:
                for ind,media in enumerate(gener.tvmedia.all()):
                    if ind > 20:
                        break
                    elif media in tv_media:
                        continue

                    rt = 0
                    genres = media.genre.all()
                    for g in genres:
                        if g not in needed:
                            needed[g] = 0
                        rt += needed[g] * 20

                    suggestion.append((round(rt/(len(genres)*100),3),media))
                    tv_media.append(media)
            
            sort = ExtraTools.quickSort(suggestion)[::-1]
            final_sort = [j for i,j in sort]
            if len(final_sort) > 100:final_sort=final_sort[:100]
            data = {}
            for ind, media in enumerate(self.serializer(final_sort,many=len(sort) > 1).data):
                data[str(ind)] = {"relativity":sort[ind][0],"media":media}
            cache.set(cache_key,data,60*60)
        return Response({"length" : len(data),"data":data})