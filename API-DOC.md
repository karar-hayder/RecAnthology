# API Endpoints Documentation

## Users API

This section documents the users-related APIs for registering users, authentication, rating media (books, TV/movies), and retrieving user genre preferences.

---

### Endpoints

#### Register New User

**POST** `/users/api/register/`

- Registers a new user.
- Required fields: `first_name`, `last_name`, `email`, `password`
- Returns the created user object or error if the email already exists.

**Example request body:**

```json
{
  "email": "user@example.com",
  "first_name": "Alex",
  "last_name": "Smith",
  "password": "your_password"
}
```

**Example response:**

```json
{
  "email": "user@example.com",
  "first_name": "Alex",
  "refreshToken": "..."
}
```

---

#### Obtain Token (Login)

**POST** `/users/api/login/`

- Returns JWT tokens for authentication.
- Fields: `email`, `password`

**Example request body:**

```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

---

#### Refresh Token

**POST** `/users/api/token/refresh/`

- Use your refresh token to get a new access token.
- See [SimpleJWT Documentation](https://django-rest-framework-simplejwt.readthedocs.io/) for details.

---

#### Rate a Book

**POST** `/users/api/books/rate/`
(*actual route may depend on project setup; see implementation*)

- Authenticated endpoint. Allows a user to create or update a book rating.
- Required fields: `book`, `rating`
  - `book`: pk/id of the Book
  - `rating`: integer from 1 to 10

**Example request body:**

```json
{
  "book": 1,
  "rating": 8
}
```

- Returns the updated/created rating.

---

#### Rate a Movie/TV Show

**POST** `/users/api/tvmedia/rate/`
(*actual route may depend on project setup; see implementation*)

- Authenticated endpoint. Allows a user to create or update a TV/movie rating.
- Required fields: `tvmedia`, `rating`
  - `tvmedia`: pk/id of the media
  - `rating`: integer from 1 to 10

**Example request body:**

```json
{
  "tvmedia": 32,
  "rating": 9
}
```

- Returns the updated/created rating.

---

#### Get User Genre Preferences

**GET** `/users/api/genre-preferences/`

- Authenticated endpoint. Returns user's book and TV/media genre preferences.
- Example response:

```json
{
  "books_genre_preferences": [
    {
      "genre": "Fantasy",
      "preference": 9.5
    },
    ...
  ],
  "tvmedia_genre_preferences": [
    {
      "genre": "Drama",
      "preference": 8.25
    },
    ...
  ]
}
```

## To be Continued with other endpoints after unifying them
