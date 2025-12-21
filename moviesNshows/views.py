from django.core.cache import cache
from django.db.models import Count
from django.views.generic import TemplateView

from .models import Genre, TvMedia


class ExploreTVMediaPage(TemplateView):
    template_name = "moviesNshows/explore_tvmedia.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # most_liked_tvmmedia = cache.get('most_liked_tvmmedia',None)
        recently_added_tvmmedia = cache.get("recently_added_tvmmedia", None)
        genres_tvmmedia = cache.get("genres_tvmmedia", None)

        if not genres_tvmmedia:
            recently_added_tvmmedia = TvMedia.objects.order_by("-startyear")[:10]
            # most_liked_tvmmedia = TvMedia.objects.annotate(likes_count=Count('liked_by')).order_by('-likes_count')[:10]

            genres = Genre.objects.annotate(tvmmedia_count=Count("tvmedia")).order_by(
                "-tvmmedia_count"
            )[:10]

            tvmmedia = TvMedia.objects.filter(genre__in=genres).distinct()
            genres_tvmmedia = {}
            for genre in genres:
                genre_tvmmedia = tvmmedia.filter(genre=genre)[:10]
                genres_tvmmedia[genre] = genre_tvmmedia

            cache.set("recently_added_tvmmedia", recently_added_tvmmedia, 60 * 60)
            # cache.set('most_liked_tvmmedia',most_liked_tvmmedia,60*60)
            cache.set("genres_tvmmedia", genres_tvmmedia, 60 * 60)

        context["recently_added_tvmmedia"] = recently_added_tvmmedia
        # context['most_liked_tvmmedia'] = most_liked_tvmmedia
        context["genres_tvmmedia"] = genres_tvmmedia

        return context
