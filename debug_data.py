import os
from collections import defaultdict

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "RecAnthology.settings")
django.setup()

from moviesNshows.models import Genre
from myutils.evaluation import train_test_split
from users.models import CustomUser, UserTvMediaRating


def debug_visibility_fast():
    print("--- Optimized Visibility Diagnostic ---")
    all_ratings = list(
        UserTvMediaRating.objects.values_list("user_id", "tvmedia_id", "rating")
    )
    train, test = train_test_split(all_ratings, 0.8, 50)

    # Map user to their high-rated test items
    user_test_hits = {}
    for u, i, r in test:
        if r >= 7:
            user_test_hits.setdefault(u, set()).add(i)

    eval_user_ids = list(user_test_hits.keys())[:50]
    print(f"Users to check: {len(eval_user_ids)}")

    # Pre-fetch genre mapping for all TV Media to avoid per-genre DB hits
    print("Pre-fetching TV catalog genres...")
    item_genres = defaultdict(set)
    for tid, gid in Genre.objects.values_list("tvmedia__id", "id"):
        if tid:
            item_genres[tid].add(gid)

    # Pre-fetch user preferences
    print("Pre-fetching user preferences...")
    user_prefs = {}
    users = CustomUser.objects.filter(pk__in=eval_user_ids).prefetch_related(
        "media_genre_preferences"
    )
    for u in users:
        # Just use the top 10 genre IDs
        user_prefs[u.pk] = list(
            u.media_genre_preferences.order_by("-preference").values_list(
                "genre_id", flat=True
            )[:10]
        )

    sum_hits_visible = 0
    total_relevant = 0

    # Simulate the gathering: For each genre, find its top items (we'll just use the first 100 items for simplicity)
    # In reality, we need to know WHICH items are in which genre.
    genre_to_items = defaultdict(list)
    for tid, gid in item_genres.items():
        for g in gid:
            if len(genre_to_items[g]) < 100:
                genre_to_items[g].append(tid)

    for uid in eval_user_ids:
        test_ids = user_test_hits[uid]
        total_relevant += len(test_ids)

        top_genre_ids = user_prefs.get(uid, [])
        visible_ids = set()
        for gid in top_genre_ids:
            visible_ids.update(genre_to_items[gid])

        overlap = test_ids.intersection(visible_ids)
        sum_hits_visible += len(overlap)
        # print(f"User {uid}: {len(test_ids)} target, {len(overlap)} visible")

    print("\nFinal Summary (50 users):")
    print(f"Total target items: {total_relevant}")
    print(
        f"Total visible to engine (Top 10 genres, Top 100 per genre): {sum_hits_visible}"
    )
    if total_relevant > 0:
        print(f"Theoretical Max Recall: {(sum_hits_visible/total_relevant)*100:.2f}%")


if __name__ == "__main__":
    debug_visibility_fast()
