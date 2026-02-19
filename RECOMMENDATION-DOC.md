# Documentation for Recommendation System Utilities

## Overview

The recommendation system is modularized into three main components:

1. **Hybrid Logic (`myutils/recommendation.py`)**: The primary entry point that combines results.
2. **Content-Based Filtering (`myutils/content_based_filtering.py`)**: Logic based on user genre preferences.
3. **Collaborative Filtering (`myutils/collaborative_filtering.py`)**: Logic based on user-item interaction patterns.

---

## Core Hybrid Logic (`myutils/recommendation.py`)

### `get_hybrid_recommendation(user, user_needed_genres, interaction_model, item_model, item_field, ...)`

- **Purpose:** Combines genre-based and collaborative filtering results into a single ranked list.
- **Key Parameters:**
  - `cf_weight`: Weight (0.0 to 1.0) for collaborative results. Default is `0.4`.
- **Exposed Functions:** This module also re-exports `get_content_based_recommendations` and `get_collaborative_recommendations` for convenience.

---

## Content-Based Filtering (`myutils/content_based_filtering.py`)

### `get_content_based_recommendations(user_needed_genres, max_num_genres, max_media_per_genre, ...)`

- **Purpose:** Generates recommendations based on the user's affinity for specific genres.
- **Internal Helper Functions:**
  - `_sort_and_select_top_genres`: Ranks genres by user preference.
  - `_calculate_media_recommendation_score`: Scores individual items based on genre overlap.
  - `_gather_recommendation_candidates`: Fetches potential matches from the database.
  - `_normalize_and_format_scores`: Scales raw scores to a 0-100 relativity rating.

---

## Collaborative Filtering (`myutils/collaborative_filtering.py`)

### `get_collaborative_recommendations(user, interaction_model, item_model, item_field, top_n=10)`

- **Purpose:** Predicts user interest by finding similar items based on global co-rating patterns.
- **Key Functions:**
  - `calculate_cosine_similarity`: Computes the angle between item rating vectors.
  - `get_item_similarities`: Identifies items with high affinity to a target item.

---

## Usage Notes

- **Primary Entry Point**: Use `get_hybrid_recommendation` for personalized user dashboards.
- **Toggling CF**: The API views support a `cf=true/false` parameter to enable or disable the collaborative component.
- **Dependency**: All utilities require Django models and appropriate rating data to function effectively.
