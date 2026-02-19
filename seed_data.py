import os
import random
import threading
import uuid

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "RecAnthology.settings")

import django

django.setup()

from Books.models import Book
from Books.models import Genre as BookGenre
from moviesNshows.models import Genre as TvGenre
from moviesNshows.models import TvMedia
from users.models import CustomUser, UserBookRating, UserTvMediaRating


def create_users(users, user_start, user_end):
    for i in range(user_start, user_end):
        email = f"user{i}@example.com"
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                "first_name": f"User{i}",
                "last_name": "Test",
                "is_active": True,
            },
        )
        if created:
            user.set_password("password123")
            user.save()
        users.append(user)


def create_books(books, bg_objs, book_start, book_end):
    for i in range(book_start, book_end):
        book = Book.objects.get_or_create(
            title=f"Sample Book {i}",
            author=f"Author {random.randint(1, 5)}",
            isbn=str(uuid.uuid4())[:13],
            description=f"Description for book {i}. " * 5,
            language="English",
            edition="1st Edition",
            pages=random.randint(100, 1000),
            likedPercent=random.randint(50, 100),
        )[0]
        # Assign 1-3 random genres
        book.genre.set(random.sample(bg_objs, random.randint(1, 3)))
        books.append(book)
        if i % 100 == 0:
            print(f"Created {i} books")


def create_tvmedia(media_list, tg_objs, media_start, media_end, types):
    for i in range(media_start, media_end):
        media = TvMedia.objects.get_or_create(
            media_type=random.choice(types),
            original_title=f"Media Title {i}",
            primary_title=f"Media Title {i}",
            over18=random.choice([True, False]),
            startyear=random.randint(1990, 2024),
            length=random.randint(20, 180),
        )[0]
        # Assign 1-3 random genres
        media.genre.set(random.sample(tg_objs, random.randint(1, 3)))
        media_list.append(media)
        if i % 100 == 0:
            print(f"Created {i} media items")


def create_ratings_chunk(users, books, media_list, user_range):
    for idx, user in enumerate(
        users[user_range[0] : user_range[1]], start=user_range[0]
    ):
        # Rate some books
        for book in random.sample(books, random.randint(10, int(len(books) * 0.2))):
            UserBookRating.objects.get_or_create(
                user=user, book=book, defaults={"rating": random.randint(1, 10)}
            )
        # Rate some TV media
        for media in random.sample(
            media_list, random.randint(10, int(len(media_list) * 0.2))
        ):
            UserTvMediaRating.objects.get_or_create(
                user=user, tvmedia=media, defaults={"rating": random.randint(1, 10)}
            )
        if idx % 20 == 0:
            print(f"Created ratings for {idx} users")


def seed():
    print("Seeding data...")

    # 1. Create Genres
    book_genres = [
        "Fiction",
        "Mystery",
        "Sci-Fi",
        "Fantasy",
        "Biography",
        "History",
        "Horror",
        "Romance",
    ]
    tv_genres = [
        "Action",
        "Comedy",
        "Drama",
        "Thriller",
        "Documentary",
        "Animation",
        "Crime",
        "Adventure",
    ]

    bg_objs = [BookGenre.objects.get_or_create(name=name)[0] for name in book_genres]
    tg_objs = [TvGenre.objects.get_or_create(name=name)[0] for name in tv_genres]

    # 2. Create Users (threaded)
    users = []
    NUM_USERS = 199
    num_threads = 4  # Tune this for your environment.
    user_threads = []
    slice_len = NUM_USERS // num_threads
    _ = [threading.Lock() for _ in range(num_threads)]

    for t in range(num_threads):
        user_start = 1 + t * slice_len
        user_end = 1 + (t + 1) * slice_len if t < num_threads - 1 else NUM_USERS + 1
        thread_users = []
        th = threading.Thread(
            target=create_users, args=(thread_users, user_start, user_end)
        )
        user_threads.append((th, thread_users))
        th.start()

    for th, partial_users in user_threads:
        th.join()
        users.extend(partial_users)

    # 3. Create Books (threaded)
    books = list(Book.objects.all())
    NUM_BOOKS = 400 - 51
    num_book_threads = 3
    slice_len_b = NUM_BOOKS // num_book_threads
    book_threads = []
    for t in range(num_book_threads):
        i_start = 51 + t * slice_len_b
        i_end = 51 + (t + 1) * slice_len_b if t < num_book_threads - 1 else 400
        thread_books = []
        th = threading.Thread(
            target=create_books, args=(thread_books, bg_objs, i_start, i_end)
        )
        book_threads.append((th, thread_books))
        th.start()
    for th, thread_books in book_threads:
        th.join()
        books.extend(thread_books)

    # 4. Create TV Media (threaded)
    media_list = list(TvMedia.objects.all())
    NUM_MEDIA = 400 - 51
    num_media_threads = 3
    slice_len_m = NUM_MEDIA // num_media_threads
    tvmedia_threads = []
    types = ["Movie", "TV Series"]

    for t in range(num_media_threads):
        m_start = 51 + t * slice_len_m
        m_end = 51 + (t + 1) * slice_len_m if t < num_media_threads - 1 else 400
        thread_media = []
        th = threading.Thread(
            target=create_tvmedia, args=(thread_media, tg_objs, m_start, m_end, types)
        )
        tvmedia_threads.append((th, thread_media))
        th.start()
    for th, thread_media in tvmedia_threads:
        th.join()
        media_list.extend(thread_media)

    books = list(set(books))
    media_list = list(set(media_list))

    # 5. Create Ratings (User Interactions, threaded by users)
    num_rating_threads = 6
    ratings_threads = []
    N_users = len(users)
    rating_chunk_size = N_users // num_rating_threads
    for t in range(num_rating_threads):
        start = t * rating_chunk_size
        end = (t + 1) * rating_chunk_size if t < num_rating_threads - 1 else N_users
        th = threading.Thread(
            target=create_ratings_chunk, args=(users, books, media_list, (start, end))
        )
        ratings_threads.append(th)
        th.start()
    for th in ratings_threads:
        th.join()

    print("Successfully seeded:")
    print(f"- {len(bg_objs)} Book Genres")
    print(f"- {len(tg_objs)} TV Genres")
    print(f"- {len(users)} Users")
    print(f"- {len(books)} Books")
    print(f"- {len(media_list)} TV Media items")
    print("Interaction ratings generated.")


if __name__ == "__main__":
    seed()
