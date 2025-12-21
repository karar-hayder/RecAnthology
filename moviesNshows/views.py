from django.core.cache import cache
from django.db.models import Count
from django.views.generic import TemplateView

from myutils.ExtraTools import get_cached_or_queryset

from .models import Genre, TvMedia


class ExploreTVMediaPage(TemplateView):
    template_name = "moviesNshows/explore_tvmedia.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Using get_cached_or_queryset for template fetching (for_template=True)
        recently_added_tvmmedia = get_cached_or_queryset(
            "recently_added_tvmmedia",
            TvMedia.objects.order_by("-startyear")[:10],
            serializer_cls=None,
            many=True,
            timeout=60 * 60,
            for_template=True,
        )

        genres = get_cached_or_queryset(
            "top10_genres_by_tvmedia_count",
            Genre.objects.annotate(tvmmedia_count=Count("tvmedia")).order_by(
                "-tvmmedia_count"
            )[:10],
            serializer_cls=None,
            many=True,
            timeout=60 * 60,
            for_template=True,
        )

        # Compose a dict of the top 10 genres mapping to up to 10 TV media in that genre
        genres_tvmmedia = cache.get("genres_tvmmedia", None)
        if not genres_tvmmedia:
            tvmmedia = TvMedia.objects.filter(genre__in=genres).distinct()
            genres_tvmmedia = {}
            for genre in genres:
                genre_tvmmedia = tvmmedia.filter(genre=genre)[:10]
                genres_tvmmedia[genre] = list(genre_tvmmedia)
            cache.set("genres_tvmmedia", genres_tvmmedia, 60 * 60)

        context["recently_added_tvmmedia"] = recently_added_tvmmedia
        context["genres_tvmmedia"] = genres_tvmmedia

        return context
