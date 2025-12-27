# Documentation for myutils/recommendation.py

## Overview

This module provides core utility functions for recommending media (TV shows, movies, books, etc.) to users based on their genre preferences.
It is designed to work with Django ORM models for `Book`, `TvMedia`, and their related `Genre` classes.
The recommendation process involves ranking genres by user preference, retrieving matching media, scoring them, and returning a normalized relativity score for each suggestion.

---

## Main Functions

### 1. `_sort_and_select_top_genres(user_genre_prefs, max_top_genres, default_preference)`

- **Purpose:**
    Sorts genre objects by user preference score and selects the top N genres.
- **Args:**
  - `user_genre_prefs`: A dictionary mapping `Genre` instances (either TV or Book genres) to float preference values.
  - `max_top_genres`: Maximum number of top genres to select.
  - `default_preference`: Default score used if a user preference is not valid/cannot be cast to float.
- **Returns:**
    List of up to `max_top_genres` genre objects with the highest user preference.

### 2. `_calculate_media_recommendation_score(media_instance, user_needed_genres, scoring_fn=None, default_value=0)`

- **Purpose:**
    Calculates a recommendation score for a single media instance (TV/Book) based on the user's needed genres.
- **Args:**
  - `media_instance`: A `TvMedia` or `Book` instance.
  - `user_needed_genres`: Dict mapping `Genre` instances to user preference scores.
  - `scoring_fn`: Optional function of the form `(genre, user_pref) -> float` to further customize scoring.
  - `default_value`: Value to use if no preference is provided.
- **Returns:**
    Tuple of `(total_score, genre_count)`, or `(0, 0)` if media has no genres.

### 3. `_gather_recommendation_candidates(relevant_genres, user_needed_genres, max_per_genre, scoring_fn=None, fallback_pref_score=0, allowed_types=("tvmedia", "books"))`

- **Purpose:**
    Finds relevant media items for a set of genres and calculates their raw recommendation scores.
- **Args:**
  - `relevant_genres`: Sequence of genres (from `_sort_and_select_top_genres`).
  - `user_needed_genres`: See above.
  - `max_per_genre`: Maximum media items to fetch per genre.
  - `scoring_fn`: Optional scoring function (see above).
  - `fallback_pref_score`: Used if a preference is missing for a genre.
  - `allowed_types`: Tuple/list of allowed related_names for object types (`'tvmedia'`, `'books'`, or both).
- **Returns:**
    Tuple containing a list: `[(score, media, genre_count), ...]` and a value for the highest score found.

### 4. `_normalize_and_format_scores(media_score_candidates, max_possible_score, decimal_places)`

- **Purpose:**
    Converts raw recommendation scores to a normalized 0–100 relativity scale.
- **Args:**
  - `media_score_candidates`: List of `(raw_score, media, genre_count)` tuples.
  - `max_possible_score`: Highest score possible in this set.
  - `decimal_places`: Number of decimals in the output relativity.
- **Returns:**
    List of `(relativity_score, media_obj)` tuples sorted by relativity (highest first).

### 5. `_build_media_recommendation(user_needed_genres, max_num_genres, max_media_per_genre, scoring_fn=None, relativity_decimals=2, default_preference_score=6, allowed_types=("tvmedia",))`

- **Purpose:**
    Orchestrates the process:
  - Selects top genres
  - Gathers candidates
  - Normalizes and returns a final suggestion list of recommendations.
- **Args:**
  - `user_needed_genres`: Dict `{Genre: preference}`
  - `max_num_genres`: How many top genres to use.
  - `max_media_per_genre`: How many items to take per genre.
  - `scoring_fn`: Optional custom scoring function.
  - `relativity_decimals`: Number of decimal places for relativity scaling.
  - `default_preference_score`: Default value for missing preferences.
  - `allowed_types`: Iterable for which related_names to allow (e.g., only `'tvmedia'` or both).
- **Returns:**
    List of `(relativity_score, media)` pairs, sorted descending by score.

---

## Usage Notes

- All functions are prefixed with an underscore, indicating they are intended for **internal** or library use.
- These utilities rely on Django ORM querysets and model relations (`genre`, `tvmedia`, `books`).
- They are designed for recommendation engines where personalized content suggestions are generated from user inputted genre preferences.

---
