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


class RateTVMediaPage(TemplateView):
    template_name = "shared/rating.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user if self.request.user.is_authenticated else None
        objs = []
        rated_dict = {}
        current_ratings = {}
        rating_numbers = list(range(1, 11))[::-1]  # For stars 1-10

        from users.models import UserTvMediaRating

        if user:
            # Find tvmedia the user has not rated yet, and current ratings for rated ones
            rated_qs = UserTvMediaRating.objects.filter(user=user)
            rated_tvmedia_ids = list(rated_qs.values_list("tvmedia_id", flat=True))
            # Current ratings for the user's ratings
            rated_ratings = {u.tvmedia_id: u.rating for u in rated_qs}
            # Get up to 30 unrated TvMedia, most recently added
            objs = list(
                TvMedia.objects.exclude(id__in=rated_tvmedia_ids).order_by(
                    "-startyear"
                )[:30]
            )
            for obj in objs:
                if obj.id in rated_ratings:
                    rated_dict[obj.id] = True
                    current_ratings[obj.id] = rated_ratings[obj.id]
                else:
                    rated_dict[obj.id] = False
                    current_ratings[obj.id] = None
        else:
            # Not authenticated: just show up to 30 by recency, with no rating
            objs = list(TvMedia.objects.all().order_by("-startyear")[:30])
            for obj in objs:
                rated_dict[obj.id] = False
                current_ratings[obj.id] = None

        context.update(
            {
                "object_list": objs,
                "object_type": "tvmedia",
                "rated_dict": rated_dict,
                "current_ratings": current_ratings,
                "rating_numbers": rating_numbers,
            }
        )
        return context


class RecommendationPage(TemplateView):
    template_name = "moviesNshows/recommendation.html"
