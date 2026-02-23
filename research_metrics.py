import os
from collections import defaultdict

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "RecAnthology.settings")
django.setup()

from myutils.collaborative_filtering import calculate_cosine_similarity
from myutils.evaluation import train_test_split
from users.models import UserBookRating, UserTvMediaRating


def research_metrics(domain="tvmedia"):
    print(f"--- Researching {domain} Stability ---")

    if domain == "tvmedia":
        rating_model = UserTvMediaRating
        item_field = "tvmedia_id"
    else:
        rating_model = UserBookRating
        item_field = "book_id"

    all_ratings = list(
        rating_model.objects.values_list("user_id", item_field, "rating")
    )
    train, test = train_test_split(all_ratings, 0.8, 42)

    # 1. Avg Ratings per User
    train_counts = defaultdict(int)
    for u, i, r in train:
        train_counts[u] += 1

    test_counts = defaultdict(int)
    for u, i, r in test:
        test_counts[u] += 1

    avg_train = sum(train_counts.values()) / len(train_counts) if train_counts else 0
    avg_test = sum(test_counts.values()) / len(test_counts) if test_counts else 0

    print(f"Avg Train Ratings per User: {avg_train:.2f}")
    print(f"Avg Test Ratings per User: {avg_test:.2f}")
    if avg_train < 5:
        print("WARNING: Low train density. CF may be unstable.")

    # 2. Similarity Matrix Density (Sample 100 items)
    print("\nMeasuring Similarity Matrix Density (Sampling 100 items)...")
    items = list(
        rating_model.objects.values_list(item_field, flat=True).distinct()[:100]
    )

    # Build item profiles for sampled items
    item_profiles = defaultdict(dict)
    ratings_for_items = rating_model.objects.filter(**{f"{item_field}__in": items})
    for r in ratings_for_items:
        item_profiles[getattr(r, item_field)][r.user_id] = r.rating

    count_non_zero = 0
    total_pairs = 0
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            sim = calculate_cosine_similarity(
                item_profiles[items[i]], item_profiles[items[j]]
            )
            if sim > 0.01:
                count_non_zero += 1
            total_pairs += 1

    density = (count_non_zero / total_pairs) * 100 if total_pairs else 0
    print(f"Sparsity check: {count_non_zero}/{total_pairs} pairs have sim > 0.01")
    print(f"Similarity Matrix Density: {density:.4f}%")
    if density < 0.1:
        print("WARNING: Near-zero density. CF might be noisy.")


if __name__ == "__main__":
    research_metrics("books")
    print("\n")
    research_metrics("tvmedia")
