# RecAnthology

## Table of Contents

* [Introduction](#introduction)
* [Features](#features)
* [Technologies Used](#technologies-used)
* [Setup and Installation](#setup-and-installation)
* [Usage](#usage)
* [API Endpoints](#api-endpoints)
* [Running Tests](#todo-running-tests)
* [Contributing](#contributing)
* [License](#license)
* [Contact](#contact)

## Introduction

> RecAnthology (Recommended Anthology) is an intelligent recommendation system designed to curate collections of books, and potentially in the future, movies and music, based on user preferences. By leveraging advanced algorithms and user feedback, RecAnthology aims to provide personalized recommendations that cater to individual tastes, making the discovery of new content seamless and enjoyable.

## Features

* User authentication and authorization using JWT
* Rate books with a likeness score from 1 to 5
* Track user genre preferences based on book ratings
* API endpoints for CRUD operations on users, books, and ratings
* Efficiently update user preferences upon new ratings

## Technologies Used

* Backend: Django, Django REST Framework
* Authentication: JWT (JSON Web Tokens)
* Database: MariaDB (for production) [SQLite could be used for development by changing some code in settings.py]
* Frontend: [None at the moment]

## Setup and Installation

### Prerequisites

* Python 3.12.3 or higher (Not sure but may work on >=3.9)
* Pipenv (or pip and virtualenv) (RECOMMENDED)
* Mariadb or any similar SQL server (SQLite3 for development)

## Installation

* Clone the repository

```sh
git clone <https://github.com/karar-hayder/RecAnthology.git>
cd RecAnthology
```

* Set up the virtual environment:(RECOMMENDED)

### Using Pipenv

```sh
python3 -m venv venv
"venv/bin/activate"
pip install -r requirements.txt
```

* Configure the database:

### Using MariaDB or similar

* Create a file in RecAnthology where the settings.py is and name it "cred.env"
* Configure the following variables to your environment:

```text
SECRET_KEY = ''## "Your secret key"
DEBUG = True ## Change to False in production
ALLOWED_HOSTS = ["*"] ## change it in production
## If you are using SQL server 
DB_NAME = "[Name]"
DB_HOST = "localhost" ## Database IP or leave it localhost if it is in the same machine
DB_PORT = 3306 ## Database Port default is 3306
DB_USER = "[USER]"
DB_PASSWORD = "[PASSWORD]"
DB_COLLATION = "utf8mb4_unicode_ci" ## If you get an error from this delete it from the settings.py
```

#### Note: you can get a django secret key by using the following command (Remove the 3 from python if you get an error and check you are using the virtual environment)

```sh
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Using SQlite3

#### Replace the following code

```py
DATABASES = {
    'default': {
        'NAME':os.environ['DB_NAME'],
        'ENGINE':'mysql.connector.django',
        'HOST':os.environ['DB_HOST'],
        'PORT':os.environ['DB_PORT'],
        'USER':os.environ['DB_USER'],
        'PASSWORD':os.environ['DB_PASSWORD'],
        'OPTIONS': {
          'autocommit': True,
          'collation':os.environ['DB_COLLATION']
        },
    }
}
```

#### With this

```py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / "db.sqlite3",
    }
}
```

* Apply migrations:

```sh
python manage.py migrate
Create a superuser:
```

* Create your admin user account

```sh

python manage.py createsuperuser
```

* Run the development server:

```sh
python manage.py runserver
```

## Usage

### (TODO) Access the API documentation

### Login and obtain a token

#### Use the provided endpoint to authenticate and obtain a JWT token for further requests to the private endpoints

### Interact with the API

#### Use tools like Postman or the REST client in VSCode to interact with the API using the endpoints described below

## API Endpoints

* Authentication
  * Register: /users/register/
  * Login: /users/login/

### Register

* Request: {"email":"(EMAIL)","first_name":"(FIRST NAME)","last_name":"(LAST NAME)","password":"(PASSWORD)"}
* Response: 201 http status if created but 409 if a user with this email exists

### Login

* Request: { "email": "(EMAIL)", "password": "(PASSWORD)" }
* Response: { "access": "jwt-access-token", "refresh": "jwt-refresh-token" }

### Logout: /users/token/refresh/ (POST)

* Request: { "refresh": "jwt-refresh-token" }

* Users
  * Create User: /users/register/ (POST)
  * Login: /users/login/ (POST)
  * Update User: /api/users/{id}/ (PUT/PATCH) (TODO)
  * Delete User: /api/users/{id}/ (DELETE) (TODO)

### General Endpoints

* Index: "/"
  * GET: Returns "OK".
  * Response: "OK"

### Genres

* All Genres: /api/genres/all/

  * GET: Retrieves all genres.
  * Response: {"data": [Genre objects]}
* Create Genre: /api/create/genre/

  * POST: Creates a new genre. Requires admin authentication.
  * Request: { "name": "Genre Name" }
  * Response:
    * 200 OK: { "data": { "id": 1, "name": "Genre Name" } } if genre already exists.
    * 201 Created: { "data": { "id": 2, "name": "New Genre Name" } } if genre is created.
    * 400 Bad Request: If the request is invalid.

### Books

* All Books: /api/allbooks/

  * GET: Retrieves the top 50 books ordered by liked percentage.
  * Response: {"data": [Book objects]}
* Create Book: /api/create/book/

  * POST: Creates a new book. Requires admin authentication.
  * Request: { "title": "Book Title", "author": "Author Name", "genre": ["Genre1", "Genre2"], ... }
  * Response:
    * 200 OK: { "data": { "id": 1, "title": "Book Title", "author": "Author Name", ... } } if book already exists.
    * 201 Created: { "data": { "id": 2, "title": "New Book Title", "author": "New Author Name", ... } } if book is created.
    * 400 Bad Request: If the request is invalid.
* Get Book: /api/get/

  * GET: Retrieves a specific book by ID.
  * Request: { "id": "Book ID" }
  * Response: { "data": { "id": "Book ID", "title": "Book Title", "author": "Author Name", ... } }
    * Error: 400 Bad Request if no ID is provided.
* Filter Books: /api/filter/

  * GET: Filters books based on title, author, and/or ID.
  * Request: { "title": "Book Title", "author": "Author Name", "id": "Book ID" }
  * Response: {"data": [Filtered Book objects]}

### Recommendations

* Public Recommend Books: /api/recommend/public/

  * POST: Provides book recommendations based on genre ratings.
  * Request: { "Genre1": rating1, "Genre2": rating2, ... }
  * Response: {"length": number_of_books, "data": { "0": { "relativity": score, "book": { ... } }, ... } }
    * Error: 406 Not Acceptable if genres are invalid.
* Private Recommend Books: /api/recommend/private/

  * GET: Provides personalized book recommendations based on user's genre preferences. Requires authentication.
  * Response: {"length": number_of_books, "data": { "0": { "relativity": score, "book": { ... } }, ... } }

### Ratings

* Rate Book: /api/rate/book/
  * POST: Allows authenticated users to rate a book.
  * Request: { "book_id": "Book ID", "rating": 1-10 }
  * Response: { "data": { "id": "Rating ID", "user": "User ID", "book": "Book ID", "rating": 1-10 } }
    * Error: 400 Bad Request if the request is invalid.

## (TODO) Running Tests

### To run the tests, use the following command

```sh
python manage.py test
```

## Contributing

* Fork the repository.
* Create a new branch: git checkout -b feature-branch-name.
* Make your changes and commit them: git commit -m 'Add some feature'.
* Push to the branch: git push origin feature-branch-name.
* Submit a pull request.

## License

### This project is licensed under the BSD-3-Clause license - see the LICENSE file for details

## Contact

### If you have any questions or feedback, feel free to reach out

#### Name: Karar Haider

#### LinkedIn: [Karar Haider](https://www.linkedin.com/in/karar-haider/)

#### GitHub: [karar-hayder](https://github.com/karar-hayder)
