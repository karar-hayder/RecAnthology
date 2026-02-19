import re
from collections import OrderedDict
from typing import Any, Dict, Type

from django.core.cache import cache
from rest_framework import serializers, status
from rest_framework.response import Response

from myutils import recommendation
from myutils.ExtraTools import get_cached_or_queryset


class GenreInputSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError("Input must be a dictionary.")
        return data


class RecommendationMixin:
    """
    Mixin to centralize common recommendation logic for Public and Private views.

    Expected on the View class:
    - model: The item model (Book or TvMedia)
    - serializer: The item serializer (BookSerializer or TvMediaSerializer)
    - item_type_key: 'book' or 'media' (string key for result entries)
    - allowed_types: tuple of types for the rec engine (e.g., ('books',))
    """

    model: Any = None
    serializer: Any = None
    item_type_key: str = "item"
    allowed_types: tuple = ("books",)

    def _resolve_genres(
        self, needed: Dict[str, Any], genre_model: Type[Any]
    ) -> OrderedDict:
        """
        Maps user-input genre names to Genre instances.
        """
        all_genres = list(genre_model.objects.all())
        alnum_map = {re.sub(r"[^a-z0-9]", "", g.name.lower()): g for g in all_genres}

        resolved = OrderedDict()
        missing = []
        ambiguous = []

        for user_key, value in needed.items():
            skey = (user_key or "").strip().lower()
            nkey = re.sub(r"[^a-z0-9]", "", skey)

            # 1. Exact case-insensitive match
            matches = [g for g in all_genres if g.name.lower() == skey]
            if not matches:
                # 2. Alphanumeric normalized match
                matches = [g for norm, g in alnum_map.items() if norm == nkey]
            if not matches:
                # 3. Substring match
                matches = [g for g in all_genres if skey and skey in g.name.lower()]

            if len(matches) == 1:
                resolved[matches[0]] = value
            elif len(matches) == 0:
                missing.append(user_key)
            else:
                ambiguous.append(user_key)

        if missing or ambiguous:
            err = {}
            if missing:
                err["not_found"] = missing
            if ambiguous:
                err["ambiguous"] = ambiguous
            raise serializers.ValidationError(
                {
                    "error": "Some genres could not be resolved.",
                    "detail": err,
                    "available_genres": sorted({g.name for g in all_genres}),
                }
            )
        return resolved

    def handle_public_recommendation(self, request, genre_model: Type[Any]) -> Response:
        """
        Shared POST handler for public recommendation views.
        """
        serializer = GenreInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )
        needed_raw = serializer.validated_data

        if len(needed_raw) > 20:
            return Response(
                {"error": f"Too many genres ({len(needed_raw)}). Max 20 allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            genre_objs = self._resolve_genres(needed_raw, genre_model)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_406_NOT_ACCEPTABLE)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_406_NOT_ACCEPTABLE)

        max_genres = 5
        max_items = 6

        suggestions = recommendation.get_content_based_recommendations(
            user_needed_genres=genre_objs,
            max_num_genres=max_genres,
            max_media_per_genre=max_items,
            relativity_decimals=1,
            default_preference_score=6,
            allowed_types=self.allowed_types,
        )

        sorted_suggestions = sorted(suggestions, key=lambda tup: tup[0], reverse=True)
        final_media = [m for _, m in sorted_suggestions][:100]
        relativity_list = [s[0] for s in sorted_suggestions][:100]

        items_data = self.serializer(final_media, many=True).data
        response_data = {}
        for idx, (rel, entry) in enumerate(zip(relativity_list, items_data)):
            response_data[str(idx)] = {"relativity": rel, self.item_type_key: entry}

        return Response({"length": len(final_media), "data": response_data})

    def handle_private_recommendation(
        self,
        request,
        genre_prefs_fn,
        interaction_model: Type[Any],
        item_field: str,
        cache_key: str,
    ) -> Response:
        """
        Shared GET handler for private recommendation views.
        """
        data = cache.get(cache_key)
        if isinstance(data, dict):
            return Response({"length": len(data), "data": data})

        needed_genres = genre_prefs_fn()
        use_cf = request.GET.get("cf", "true").lower() == "true"

        if not needed_genres:
            # Simple fallback sorting
            order_field = (
                "-likedPercent" if hasattr(self.model, "likedPercent") else "-startyear"
            )
            items = self.model.objects.order_by(order_field)[:100]
            items_data = self.serializer(items, many=True).data
            response_data = {
                str(idx): {
                    "relativity": None,
                    getattr(self, "item_type_key", "item"): entry,
                }
                for idx, entry in enumerate(items_data)
            }
            return Response({"length": len(items_data), "data": response_data})

        if use_cf:
            hybrid_results = recommendation.get_hybrid_recommendation(
                user=request.user,
                user_needed_genres=needed_genres,
                interaction_model=interaction_model,
                item_model=self.model,
                item_field=item_field,
                top_n=100,
                allowed_types=getattr(self, "allowed_types", ("books",)),
            )
            final_media = [item for _, item in hybrid_results]
            relativity_list = [score for score, _ in hybrid_results]
        else:
            suggestions = recommendation.get_content_based_recommendations(
                user_needed_genres=needed_genres,
                max_num_genres=10,
                max_media_per_genre=21,
                relativity_decimals=1,
                default_preference_score=6,
                allowed_types=getattr(self, "allowed_types", ("books",)),
            )
            sorted_suggestions = sorted(
                suggestions, key=lambda tup: tup[0], reverse=True
            )
            final_media = [b for _, b in sorted_suggestions][:100]
            relativity_list = [s[0] for s in sorted_suggestions][:100]

        items_data = self.serializer(final_media, many=True).data
        response_data = {}
        for idx, (rel, entry) in enumerate(zip(relativity_list, items_data)):
            response_data[str(idx)] = {
                "relativity": rel,
                getattr(self, "item_type_key", "item"): entry,
            }

        cache.set(cache_key, response_data, 60 * 60)
        return Response({"length": len(response_data), "data": response_data})


class BaseCRUDMixin:
    """
    Mixin for simple list/create operations.
    Requires: model, serializer
    """

    model: Any = None
    serializer: Any = None

    def handle_list(self, cache_key: str, timeout: int = 3600) -> Response:
        data = get_cached_or_queryset(
            cache_key,
            self.model.objects.all(),
            self.serializer,
            many=True,
            timeout=timeout,
        )
        return Response({"data": data})

    def handle_create(self, request) -> Response:
        serializer = self.serializer(data=request.data)
        if serializer.is_valid():
            in_db = self.model.objects.filter(**serializer.validated_data)
            if in_db.exists():
                return Response(
                    {"data": self.serializer(in_db.first()).data},
                    status=status.HTTP_200_OK,
                )
            new_obj = serializer.save()
            return Response(
                {"data": self.serializer(new_obj).data}, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
