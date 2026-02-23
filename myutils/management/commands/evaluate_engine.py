"""
Management command to evaluate the recommendation engine offline.

Usage:
    python manage.py evaluate_engine [--k 10] [--split 0.8] [--seed 42]
"""

import time

from django.core.management.base import BaseCommand

from Books.models import Book
from moviesNshows.models import TvMedia
from myutils.evaluation import evaluate_recommendations, train_test_split
from myutils.recommendation import get_hybrid_recommendation
from users.models import (
    CustomUser,
    UserBookRating,
    UserBooksGenrePreference,
    UserTvMediaRating,
)


class Command(BaseCommand):
    help = "Run offline evaluation of the recommendation engine"

    def add_arguments(self, parser):
        parser.add_argument(
            "--k", type=int, default=10, help="Top-K cutoff for metrics (default: 10)"
        )
        parser.add_argument(
            "--split",
            type=float,
            default=0.8,
            help="Train/test split ratio (default: 0.8)",
        )
        parser.add_argument(
            "--seed", type=int, default=42, help="Random seed (default: 42)"
        )
        parser.add_argument(
            "--mode",
            type=str,
            choices=["hybrid", "content", "popularity"],
            default="hybrid",
            help="Evaluation mode (default: hybrid)",
        )

    def handle(self, *args, **options):
        k = options["k"]
        split_ratio = options["split"]
        seed = options["seed"]
        mode = options["mode"]

        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(
            self.style.NOTICE("RecAnthology — Offline Recommendation Evaluation")
        )
        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(f"  K={k}  split={split_ratio}  seed={seed}  mode={mode}\n")

        times = {}

        # --- Books evaluation ---
        self.stdout.write(self.style.HTTP_INFO("\n--- Books Evaluation ---"))
        t0 = time.time()
        book_metrics = self._evaluate_domain(
            rating_model=UserBookRating,
            item_model=Book,
            item_field="book",
            genre_pref_model=UserBooksGenrePreference,
            genre_fk="genre",
            k=k,
            split_ratio=split_ratio,
            seed=seed,
        )
        t1 = time.time()
        times["books"] = t1 - t0
        self._print_metrics(book_metrics)
        self.stdout.write(
            self.style.NOTICE(f"  Books evaluation time: {times['books']:.2f}s")
        )

        # --- TV Media evaluation ---
        self.stdout.write(self.style.HTTP_INFO("\n--- TV Media Evaluation ---"))
        t2 = time.time()
        tv_metrics = self._evaluate_domain(
            rating_model=UserTvMediaRating,
            item_model=TvMedia,
            item_field="tvmedia",
            genre_pref_model=None,  # Will use media genre prefs
            genre_fk="genre",
            k=k,
            split_ratio=split_ratio,
            seed=seed,
        )
        t3 = time.time()
        times["tv_media"] = t3 - t2
        self._print_metrics(tv_metrics)
        self.stdout.write(
            self.style.NOTICE(f"  TV Media evaluation time: {times['tv_media']:.2f}s")
        )

        total_time = t3 - t0
        self.stdout.write(
            self.style.NOTICE(f"\nTotal evaluation time: {total_time:.2f}s")
        )
        self.stdout.write(self.style.SUCCESS("\nEvaluation complete."))

    def _evaluate_domain(
        self,
        rating_model,
        item_model,
        item_field,
        genre_pref_model,
        genre_fk,
        k,
        split_ratio,
        seed,
        mode="hybrid",
    ):
        # Collect all ratings as (user_id, item_id, rating)
        all_ratings = list(
            rating_model.objects.values_list("user_id", f"{item_field}_id", "rating")
        )

        if len(all_ratings) < 10:
            self.stdout.write(
                self.style.WARNING(
                    f"  Not enough ratings ({len(all_ratings)}). Skipping."
                )
            )
            return {"precision_at_k": 0.0, "recall_at_k": 0.0, "ndcg_at_k": 0.0}

        self.stdout.write(f"  Total ratings: {len(all_ratings)}")

        train_set, test_set = train_test_split(all_ratings, split_ratio, seed)
        self.stdout.write(f"  Train: {len(train_set)}, Test: {len(test_set)}")

        # Build test ground truth: items each user rated >= 7 in the test set
        user_relevant = {}
        for user_id, item_id, rating in test_set:
            if rating >= 7:
                user_relevant.setdefault(user_id, set()).add(item_id)

        # Build train-only item IDs per user so CF can still recommend test items
        train_items_by_user = {}
        for user_id, item_id, _ in train_set:
            train_items_by_user.setdefault(user_id, set()).add(item_id)

        # Generate recommendations for each user who has test data
        users_to_eval = list(user_relevant.keys())[:50]  # Limit for speed
        self.stdout.write(f"  Evaluating {len(users_to_eval)} users...")

        user_recommendations = {}
        eval_start = time.time()
        for user_id in users_to_eval:
            try:
                user = CustomUser.objects.get(pk=user_id)
            except CustomUser.DoesNotExist:
                continue

            # Get user's genre preferences
            if item_field == "book":
                genre_prefs = user.get_books_genre_preferences()
            else:
                genre_prefs = user.get_media_genre_preferences()

            if not genre_prefs:
                continue

            try:
                # Exclude only train items so that test items remain recommendable
                already_rated = train_items_by_user.get(user_id, set())

                if mode == "content":
                    from myutils.content_based_filtering import (
                        get_content_based_recommendations,
                    )

                    if item_field == "book":
                        allowed_types = ("books",)
                    else:
                        allowed_types = ("tvmedia",)
                    recs = get_content_based_recommendations(
                        user_needed_genres=genre_prefs,
                        max_num_genres=30,
                        max_media_per_genre=100,
                        allowed_types=allowed_types,
                        user=user,
                        item_field=item_field,
                        already_rated=already_rated,
                    )
                elif mode == "popularity":
                    from django.db.models import Count

                    rating_lookup = (
                        "userbookrating"
                        if item_field == "book"
                        else "usertvmediarating"
                    )
                    # Simple popularity baseline: most rated items in the whole catalog
                    pop_items = (
                        item_model.objects.exclude(pk__in=already_rated)
                        .annotate(num_ratings=Count(rating_lookup))
                        .order_by("-num_ratings")[: k * 10]
                    )
                    recs = [(0.0, item) for item in pop_items]
                else:
                    recs = get_hybrid_recommendation(
                        user=user,
                        user_needed_genres=genre_prefs,
                        interaction_model=rating_model,
                        item_model=item_model,
                        item_field=item_field,
                        top_n=k * 10,
                        already_rated=already_rated,
                    )
                user_recommendations[user_id] = [item.pk for _, item in recs]
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  Skipped user {user_id}: {e}"))
        eval_end = time.time()
        self.stdout.write(
            self.style.NOTICE(
                f"  Recommendation generation time: {eval_end - eval_start:.2f}s"
            )
        )

        return evaluate_recommendations(user_recommendations, user_relevant, k)

    def _print_metrics(self, metrics):
        self.stdout.write(f"  Precision@K:  {metrics['precision_at_k']:.4f}")
        self.stdout.write(f"  Recall@K:     {metrics['recall_at_k']:.4f}")
        self.stdout.write(f"  NDCG@K:       {metrics['ndcg_at_k']:.4f}")
