import os
import random
import uuid
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "RecAnthology.settings")

import django

django.setup()
from django.utils import timezone
from users.models import CustomUser, UserBookRating, UserTvMediaRating
from Books.models import Book, Genre as BookGenre
from moviesNshows.models import TvMedia, Genre as TvGenre


def seed():
    print("Seeding data...")
    
    # 1. Create Genres
    book_genres = ["Fiction", "Mystery", "Sci-Fi", "Fantasy", "Biography", "History", "Horror", "Romance"]
    tv_genres = ["Action", "Comedy", "Drama", "Thriller", "Documentary", "Animation", "Crime", "Adventure"]
    
    bg_objs = [BookGenre.objects.get_or_create(name=name)[0] for name in book_genres]
    tg_objs = [TvGenre.objects.get_or_create(name=name)[0] for name in tv_genres]
    
    # 2. Create Users
    users = []
    for i in range(1, 20):
        email = f"user{i}@example.com"
        user, created = CustomUser.objects.get_or_create(
            email=email,
            defaults={
                "first_name": f"User{i}",
                "last_name": f"Test",
                "is_active": True
            }
        )
        if created:
            user.set_password("password123")
            user.save()
        users.append(user)
        
    # 3. Create Books
    books = []
    for i in range(15, 40):
        book = Book.objects.create(
            title=f"Sample Book {i}",
            author=f"Author {random.randint(1, 5)}",
            isbn=str(uuid.uuid4())[:13],
            description=f"Description for book {i}. " * 5,
            language="English",
            edition="1st Edition",
            pages=random.randint(100, 1000),
            likedPercent=random.randint(50, 100)
        )
        # Assign 1-3 random genres
        book.genre.set(random.sample(bg_objs, random.randint(1, 3)))
        books.append(book)
        
    # 4. Create TV Media
    media_list = []
    types = ["Movie", "TV Series"]
    for i in range(15, 40):
        media = TvMedia.objects.create(
            media_type=random.choice(types),
            original_title=f"Media Title {i}",
            primary_title=f"Media Title {i}",
            over18=random.choice([True, False]),
            startyear=random.randint(1990, 2024),
            length=random.randint(20, 180)
        )
        # Assign 1-3 random genres
        media.genre.set(random.sample(tg_objs, random.randint(1, 3)))
        media_list.append(media)
        
    # 5. Create Ratings (User Interactions)
    for user in users:
        # Rate some books
        for book in random.sample(books, random.randint(5, 10)):
            UserBookRating.objects.get_or_create(
                user=user,
                book=book,
                defaults={"rating": random.randint(1, 10)}
            )
        # Rate some TV media
        for media in random.sample(media_list, random.randint(5, 10)):
            UserTvMediaRating.objects.get_or_create(
                user=user,
                tvmedia=media,
                defaults={"rating": random.randint(1, 10)}
            )
            
    print(f"Successfully seeded:")
    print(f"- {len(bg_objs)} Book Genres")
    print(f"- {len(tg_objs)} TV Genres")
    print(f"- {len(users)} Users")
    print(f"- {len(books)} Books")
    print(f"- {len(media_list)} TV Media items")
    print("Interaction ratings generated.")

if __name__ == "__main__":
    seed()
