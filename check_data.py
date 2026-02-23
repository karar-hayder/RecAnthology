"""
Check database for data anomalies that could cause very low precision/recall/ndcg in recommendation evaluation.

Anomalies we want to check for:
- Users with zero or very few ratings.
- Items (books/media) with zero or very few ratings.
- Highly unbalanced distributions: e.g., some books/media with tons of ratings, vast majority with none/few.
- Ratings distributions: All users rating the same items, or rating distributions skewed (like all 1s/10s).
- Genre assignments: Items without genres, genres without any associated items, users without genre preferences.
- Orphaned genre preference records (no corresponding user or genre).
- Duplicate ratings.
- Anything else plausible.

Prints summary stats and suspicious cases.
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "RecAnthology.settings")
import django

django.setup()

from django.db.models import Avg, Count, Max, Min

from Books.models import Book
from Books.models import Genre as BookGenre
from moviesNshows.models import Genre as TvGenre
from moviesNshows.models import TvMedia
from users.models import (
    CustomUser,
    UserBookRating,
    UserBooksGenrePreference,
    UserTvMediaGenrePreference,
    UserTvMediaRating,
)


def check_db_anomalies():
    print("==== DB ANOMALY CHECK ====")

    # --- Users ---
    total_users = CustomUser.objects.count()
    print(f"Total users: {total_users}")

    # Users with NO book ratings
    users_no_book_ratings = CustomUser.objects.annotate(rc=Count("rated_books")).filter(
        rc=0
    )
    print(f"Users with 0 book ratings: {users_no_book_ratings.count()}")
    if users_no_book_ratings.count() > 0:
        print(f"  Example (up to 5): {[u.email for u in users_no_book_ratings[:5]]}")

    # Users with NO tvmedia ratings
    users_no_tv_ratings = CustomUser.objects.annotate(rc=Count("rated_tvmedia")).filter(
        rc=0
    )
    print(f"Users with 0 tvmedia ratings: {users_no_tv_ratings.count()}")
    if users_no_tv_ratings.count() > 0:
        print(f"  Example (up to 5): {[u.email for u in users_no_tv_ratings[:5]]}")

    # Users with very few ratings
    few_threshold = 5
    u_few_books = CustomUser.objects.annotate(rc=Count("rated_books")).filter(
        rc__lte=few_threshold
    )
    print(f"Users with <= {few_threshold} book ratings: {u_few_books.count()}")

    u_few_tv = CustomUser.objects.annotate(rc=Count("rated_tvmedia")).filter(
        rc__lte=few_threshold
    )
    print(f"Users with <= {few_threshold} tvmedia ratings: {u_few_tv.count()}")

    # --- Books / TV Media ---
    total_books = Book.objects.count()
    total_tvmedia = TvMedia.objects.count()
    print(f"Total books: {total_books} | Total tvmedia: {total_tvmedia}")

    # Items w/ no ratings
    books_no_ratings = Book.objects.annotate(rc=Count("userbookrating")).filter(rc=0)
    print(f"Books with 0 ratings: {books_no_ratings.count()}")
    if books_no_ratings.count() > 0:
        print(f"  Example: {[b.title for b in books_no_ratings[:5]]}")

    tvmedia_no_ratings = TvMedia.objects.annotate(rc=Count("usertvmediarating")).filter(
        rc=0
    )
    print(f"TV Media with 0 ratings: {tvmedia_no_ratings.count()}")
    if tvmedia_no_ratings.count() > 0:
        print(f"  Example: {[m.original_title for m in tvmedia_no_ratings[:5]]}")

    # Items w/ very few ratings
    b_few_ratings = Book.objects.annotate(rc=Count("userbookrating")).filter(
        rc__lte=few_threshold
    )
    print(f"Books with <= {few_threshold} ratings: {b_few_ratings.count()}")
    t_few_ratings = TvMedia.objects.annotate(rc=Count("usertvmediarating")).filter(
        rc__lte=few_threshold
    )
    print(f"TV Media with <= {few_threshold} ratings: {t_few_ratings.count()}")

    # Highly rated items
    max_book_ratings = Book.objects.annotate(rc=Count("userbookrating")).order_by(
        "-rc"
    )[:5]
    print("Books w/ most ratings (top 5):")
    for b in max_book_ratings:
        print(f"  '{b.title}'  | ratings: {b.rc}")

    max_tv_ratings = TvMedia.objects.annotate(rc=Count("usertvmediarating")).order_by(
        "-rc"
    )[:5]
    print("TV Media w/ most ratings (top 5):")
    for m in max_tv_ratings:
        print(f"  '{m.original_title}' | ratings: {m.rc}")

    # --- Duplicated ratings ---
    dbl_ratings = (
        UserBookRating.objects.values("user", "book")
        .annotate(c=Count("id"))
        .filter(c__gt=1)
    )
    tv_dbl = (
        UserTvMediaRating.objects.values("user", "tvmedia")
        .annotate(c=Count("id"))
        .filter(c__gt=1)
    )
    if dbl_ratings:
        print("WARNING: Duplicate book ratings found (user, book):")
        for row in dbl_ratings[:5]:
            print(f"  user={row['user']} book={row['book']} count={row['c']}")
    if tv_dbl:
        print("WARNING: Duplicate TV ratings found (user, tvmedia):")
        for row in tv_dbl[:5]:
            print(f"  user={row['user']} tvmedia={row['tvmedia']} count={row['c']}")

    # --- Ratings stats ---
    book_rating_stats = UserBookRating.objects.aggregate(
        Avg("rating"), Min("rating"), Max("rating")
    )
    tv_rating_stats = UserTvMediaRating.objects.aggregate(
        Avg("rating"), Min("rating"), Max("rating")
    )
    print(
        f"Book ratings stats: avg={book_rating_stats['rating__avg']:.2f}, min={book_rating_stats['rating__min']}, max={book_rating_stats['rating__max']}"
    )
    print(
        f"TV media ratings stats: avg={tv_rating_stats['rating__avg']:.2f}, min={tv_rating_stats['rating__min']}, max={tv_rating_stats['rating__max']}"
    )

    # Distribution check: Print a little histogram for book and tv ratings
    from collections import Counter

    c_book = Counter(UserBookRating.objects.values_list("rating", flat=True))
    c_tv = Counter(UserTvMediaRating.objects.values_list("rating", flat=True))
    print("Book ratings distribution:")
    for i in range(1, 11):
        print(f"  {i}: {c_book.get(i, 0)}")
    print("TV ratings distribution:")
    for i in range(1, 11):
        print(f"  {i}: {c_tv.get(i, 0)}")

    # --- Genre assignments ---
    bg_total = BookGenre.objects.count()
    tg_total = TvGenre.objects.count()
    print(f"Book genres: {bg_total}")
    print(f"TV genres: {tg_total}")

    # Book genres with 0 books: The field is 'books', not 'book'
    no_books_in_genre = BookGenre.objects.annotate(cnt=Count("books")).filter(cnt=0)
    print(f"Book genres with 0 books: {no_books_in_genre.count()}")

    # TV genres with 0 tvmedia: The field is 'tvmedia', not 'tvmedias'
    no_tv_in_genre = TvGenre.objects.annotate(cnt=Count("tvmedia")).filter(cnt=0)
    print(f"TV genres with 0 tvmedia: {no_tv_in_genre.count()}")

    books_no_genre = Book.objects.annotate(cnt=Count("genre")).filter(cnt=0)
    print(f"Books with 0 genres: {books_no_genre.count()}")
    tv_no_genre = TvMedia.objects.annotate(cnt=Count("genre")).filter(cnt=0)
    print(f"TVMedia with 0 genres: {tv_no_genre.count()}")

    # --- User genre preferences ---
    users_no_book_prefs = CustomUser.objects.annotate(
        rc=Count("books_genre_preferences")
    ).filter(rc=0)
    users_no_tv_prefs = CustomUser.objects.annotate(
        rc=Count("media_genre_preferences")
    ).filter(rc=0)
    print(f"Users w/ 0 book genre preferences: {users_no_book_prefs.count()}")
    print(f"Users w/ 0 tvmedia genre preferences: {users_no_tv_prefs.count()}")

    # Check for genre prefs with dead users or genres
    missing_bprefs = (
        UserBooksGenrePreference.objects.filter(user__isnull=True).count()
        + UserBooksGenrePreference.objects.filter(genre__isnull=True).count()
    )
    missing_tprefs = (
        UserTvMediaGenrePreference.objects.filter(user__isnull=True).count()
        + UserTvMediaGenrePreference.objects.filter(genre__isnull=True).count()
    )
    print(f"UserBooksGenrePreference with NULL user/genre: {missing_bprefs}")
    print(f"UserTvMediaGenrePreference with NULL user/genre: {missing_tprefs}")

    # Orphaned genre prefs
    dead_users = CustomUser.objects.all().values_list("id", flat=True)
    orphaned_book_prefs = UserBooksGenrePreference.objects.exclude(
        user_id__in=dead_users
    ).count()
    orphaned_tv_prefs = UserTvMediaGenrePreference.objects.exclude(
        user_id__in=dead_users
    ).count()
    print(f"Orphaned book genre prefs (user doesn't exist): {orphaned_book_prefs}")
    print(f"Orphaned tv genre prefs (user doesn't exist): {orphaned_tv_prefs}")

    print("==== END DB ANOMALY CHECK ====")


if __name__ == "__main__":
    check_db_anomalies()
