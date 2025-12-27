# RecAnthology

## Table of Contents

* [Introduction](#introduction)
* [Features](#features)
* [Technologies Used](#technologies-used)
* [Setup and Installation](#setup-and-installation)
* [Usage](#usage)
* [API Endpoints](#api-endpoints)
* [Running Tests](#running-tests)
* [Contributing](#contributing)
* [License](#license)
* [Contact](#contact)

## Introduction

> RecAnthology (Recommended Anthology) is an intelligent recommendation system designed to curate collections of books, movies, and TV shows based on user preferences. By leveraging advanced algorithms and user feedback, RecAnthology aims to provide personalized recommendations that cater to individual tastes, making the discovery of new content seamless and enjoyable. The latest version includes expanded content, improved performance, and enhanced user management features.

## Features

* User authentication and authorization using JWT
* Rate books, movies, and TV shows with a rating system
* Track user genre preferences based on ratings
* API endpoints for CRUD operations on users, books, movies, and TV shows
* Personalized recommendations based on user preferences and feedback
* Added caching for improved performance
* Comprehensive model testing for error detection
* Enhanced data validation logic

## Technologies Used

* Backend: Django, Django REST Framework
* Authentication: Secure user authentication and authorization with JWT (JSON Web Tokens) and Django authentication
* Database: PostGreSQL (for production) [SQLite could be used for development by changing some code in settings.py]
* Frontend: Django templates with Bootstrap 5 (see [`templates/base.html`](templates/base.html))

## Recommendation System Overview

### Content-Based Recommendation

RecAnthology primarily uses a **content-based recommendation** engine that leverages user preferences for genres to suggest books, TV shows, and movies that are most likely to match their tastes.

**How It Works:**

* Users rate media items, and these ratings are used to infer their genre preferences.
* The system identifies the genres a user favors the most.
* For each top genre, a set of relevant media is selected (from both books and TV/media, as configured).
* Recommendation scores are calculated for each media item based on how well its genres align with the user's preferences. Optionally, a custom scoring function can further personalize the scores.
* Scores are normalized into a 0–100 scale, providing a relativity metric so users see which recommendations are strongest.
* The final recommendation list is sorted by this relativity score.

See the [RECOMMENDATION-DOC.md](./RECOMMENDATION-DOC.md) for detailed documentation on each function and example usage scenarios.

### Collaborative Filtering

[TODO: Collaborative filtering recommendation system will be added here in the future.]

## Setup and Installation

### Prerequisites

* Python 3.12.3 or higher (Not sure but may work on >=3.9)
* Pipenv (or pip and virtualenv) (RECOMMENDED)
* PostGreSQL or any similar SQL server (SQLite3 for development)

## Installation

* Clone the repository

```sh
git clone <https://github.com/karar-hayder/RecAnthology.git>
cd RecAnthology
```

* Set up the virtual environment (RECOMMENDED):

### Using Pipenv

#### On Linux / macOS

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### On Windows

```sh
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

* Configure the database:

### Using PostGreSQL or similar

* Create a file in RecAnthology where the settings.py is and name it "cred.env"
* Configure the following variables to your environment:

```env
SECRET_KEY=your_secret_key_here
DEBUG=True  # Change to False in production
ALLOWED_HOSTS=localhost,127.0.0.1  # Comma-separated; change for production
ADMIN_PAGE=admin/  # Change admin page URL in production
DB_NAME=your_db_name
DB_HOST=localhost  # Use database IP or localhost
DB_PORT=5432  # Default PostGreSQL
DB_USER=your_db_user
DB_PASSWORD=your_db_password
REDIS_URL=redis://localhost:6379/0  # Optional; defaults to local Redis.

```

#### Note: you can get a django secret key by using the following command (Remove the 3 from python if you get an error and check you are using the virtual environment)

```sh
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Using SQlite3

#### Replace the following code

```py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_env("DB_NAME"),
        'HOST': get_env("DB_HOST"),
        'PORT': get_env("DB_PORT"),
        'USER': get_env("DB_USER"),
        'PASSWORD': get_env("DB_PASSWORD"),
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

## API Endpoints

See [API-DOC.md](./API-DOC.md) for complete documentation of all endpoints.

## Running Tests

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
