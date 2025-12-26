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
* Expanded content with over 50k movies and shows, and up to 6k books
* Added caching for improved performance
* Comprehensive model testing for error detection
* Enhanced data validation logic

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
ADMIN_PAGE = "admin/" ## Admin page url change in production
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
