# RecAnthology

## Table of Contents

- [RecAnthology](#recanthology)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Core Capabilities](#core-capabilities)
  - [Technologies Used](#technologies-used)
  - [System Design \& Architecture](#system-design--architecture)
    - [Constraints \& Trade-offs](#constraints--trade-offs)
  - [Recommendation Engine Design](#recommendation-engine-design)
    - [Content-Based Recommendation](#content-based-recommendation)
    - [Collaborative Filtering](#collaborative-filtering)
  - [Setup and Installation](#setup-and-installation)
    - [Prerequisites](#prerequisites)
  - [Installation](#installation)
    - [Using Pipenv](#using-pipenv)
      - [On Linux / macOS](#on-linux--macos)
      - [On Windows](#on-windows)
    - [Using PostgreSQL or Equivalent](#using-postgresql-or-equivalent)
      - [To generate a Django secret key](#to-generate-a-django-secret-key)
    - [Using SQLite3 (Development Only)](#using-sqlite3-development-only)
      - [Replace the following code in `settings.py`](#replace-the-following-code-in-settingspy)
      - [With this configuration](#with-this-configuration)
  - [Usage](#usage)
  - [API Endpoints](#api-endpoints)
  - [Running Tests](#running-tests)
  - [Contributing](#contributing)
  - [License](#license)
  - [Contact](#contact)

## Introduction

> RecAnthology (Recommended Anthology) is an intelligent, extensible recommendation platform engineered to curate collections of books, movies, and TV shows tailored to user preferences. Leveraging advanced algorithms and continuous user feedback, RecAnthology delivers personalized, dynamic recommendations that optimize content discovery. The most recent release expands media coverage, maximizes performance via caching, and improves user management for system stability.

## Core Capabilities

- Robust user authentication and authorization powered by JWT
- Flexible rating system for books, movies, and TV shows
- Real-time tracking and modeling of user genre preferences
- Comprehensive API endpoints supporting CRUD operations on users and media assets
- Adaptive, feedback-driven recommendation algorithms
- Integrated caching layer for enhanced throughput and latency reduction
- Automated model testing and error detection
- Strict data validation pipelines

## Technologies Used

- **Backend:** Django, Django REST Framework
- **Authentication:** JWT and Django authentication modules
- **Database:** PostgreSQL (production); SQLite as a lightweight development alternative (configurable in `settings.py`)
- **Frontend:** Django templates using Bootstrap 5 (see [`templates/base.html`](templates/base.html))

## System Design & Architecture

RecAnthology's architecture is modular and designed for scalability, maintainability, and extensibility.

- **API Layer:** Serves all client interactions via RESTful routes.
- **Authentication:** Stateless JWT ensures secure, scalable user sessions.
- **Recommendation Engine:** Pluggable, supports both content-based and collaborative filtering modules.
- **Service Layer:** Encapsulates business logic, data aggregation, scoring, and caching.
- **Data Layer:** Relational data managed in PostgreSQL, with optional support for Redis-based caching.
- **Frontend:** Server-rendered templates enable rapid UI prototyping and integration.

### Constraints & Trade-offs

- **Performance vs. Flexibility:** While Django REST and PostgreSQL provide robust scalability, they require careful query optimization for recommendation workloads. SQLite is practical for development but not suited for production scale or concurrent writes.
- **Real-Time Recommendations:** On-the-fly scoring enhances personalization but introduces higher compute overhead. Background jobs (optional future enhancement) may be leveraged for offline pre-computation at scale.
- **Caching:** The addition of caching (e.g., Redis) accelerates common queries but demands cache invalidation strategies when user preferences or media data change.
- **Extensibility:** Modular engine design facilitates new recommendation algorithms but may increase initial development complexity.

## Recommendation Engine Design

### Content-Based Recommendation

RecAnthology implements a **content-based recommendation** engine, aligning users with media selections based on explicit and inferred genre affinities.

**Operational Overview:**

- Users rate media items, directly shaping a user-genre affinity profile.
- Dominant user genres are dynamically detected and ranked.
- Media candidates relevant to user profiles are identified from the global content pool.
- A scoring algorithm evaluates the alignment between item genres and each user, weighting scores optionally with custom logic.
- Scores are normalized (0–100) for intuitive relativity and transparent system output.
- The final recommendation list is strictly sorted by these normalized scores.

For comprehensive implementation and advanced usage, refer to [RECOMMENDATION-DOC.md](./RECOMMENDATION-DOC.md).

### Collaborative Filtering

RecAnthology is scheduled to evolve its recommendation engine with **collaborative filtering** capabilities in the next major development cycle. The plan includes:

1. **Data Aggregation**: Capture and anonymize cross-user rating histories for shared affinity modeling.
2. **Similarity Computation**: Implement user-user and item-item similarity matrices using proven algorithms (e.g., cosine similarity).
3. **Hybrid Scoring Engine**: Integrate collaborative outputs with the existing content-based system, allowing for hybrid recommendation strategies.
4. **Performance Optimization**: Profile and optimize for batch computation, including possible offline background jobs.
5. **A/B Testing & Evaluation**: Deploy collaborative models incrementally and monitor accuracy, coverage, and system resource consumption.
6. **Documentation & API Exposure**: Update usage guides and API documentation to expose new endpoints and engine capabilities.

## Setup and Installation

### Prerequisites

- Python 3.12.3 or newer (should run on >=3.9)
- Pipenv (or pip and virtualenv) **(RECOMMENDED)**
- PostgreSQL or any comparable SQL server (SQLite3 supported for development only)

## Installation

- Clone the repository:

```sh
git clone <https://github.com/karar-hayder/RecAnthology.git>
cd RecAnthology
```

- Set up the virtual environment (recommended):

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

- Configure the database:

### Using PostgreSQL or Equivalent

- Create a file in the RecAnthology directory (next to `settings.py`) and name it `cred.env`
- Set the following variables:

```env
SECRET_KEY=your_secret_key_here
DEBUG=True  # Set to False in production
ALLOWED_HOSTS=localhost,127.0.0.1  # Comma-separated; update for production deployment
ADMIN_PAGE=admin/  # Customize admin URL in production environments
DB_NAME=your_db_name
DB_HOST=localhost  # DB server IP or localhost
DB_PORT=5432  # Default for PostgreSQL
DB_USER=your_db_user
DB_PASSWORD=your_db_password
REDIS_URL=redis://localhost:6379/0  # Optional. Defaults to local Redis instance.
```

#### To generate a Django secret key

```sh
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Using SQLite3 (Development Only)

#### Replace the following code in `settings.py`

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

#### With this configuration

```py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / "db.sqlite3",
    }
}
```

- Apply migrations:

```sh
python manage.py migrate
Create a superuser:
```

- Create your admin user account

```sh
python manage.py createsuperuser
```

- Launch the development server:

```sh
python manage.py runserver
```

## Usage

## API Endpoints

The full API documentation, including endpoint specifications and authentication protocols, is provided in [API-DOC.md](./API-DOC.md).

## Running Tests

To execute the automated test suite, run:

```sh
python manage.py test
```

## Contributing

- Fork the repository.
- Create a new branch: `git checkout -b feature-branch-name`
- Commit your changes: `git commit -m 'Add some feature'`
- Push to your branch: `git push origin feature-branch-name`
- Open a pull request.

## License

This project is released under the BSD-3-Clause license. See the LICENSE file for full details.

## Contact

For questions or feedback, contact:

- **Name:** Karar Haider
- **LinkedIn:** [Karar Haider](https://www.linkedin.com/in/karar-haider/)
- **GitHub:** [karar-hayder](https://github.com/karar-hayder)
