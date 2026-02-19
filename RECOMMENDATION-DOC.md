# Documentation for Recommendation System Utilities

## Overview

The recommendation system is modularized into five main components:

1. **Hybrid Logic (`myutils/recommendation.py`)**: The primary entry point that combines results using a formal scoring equation.
2. **Content-Based Filtering (`myutils/content_based_filtering.py`)**: Logic based on user genre preferences.
3. **Collaborative Filtering (`myutils/collaborative_filtering.py`)**: Logic based on user-item interaction patterns, with Redis-cached similarity matrices.
4. **Cold-Start Strategies (`myutils/cold_start.py`)**: Handles new users and new items.
5. **Evaluation Metrics (`myutils/evaluation.py`)**: Offline recommendation quality measurement.

6. **Feature Signals (`myutils/feature_signals.py`)**: Computes per-item bonus scores from metadata (author, popularity, recency, etc.).

---

## Hybrid Scoring Equation

The engine combines content-based and collaborative signals using a weighted formula:

**FinalScore = α · C<sub>content</sub> + (1 - α) · C<sub>cf</sub>**

Where:

- `C_content` — Content-based score (Genre Affinity + Feature Signals)
- `C_cf` — Collaborative filtering score (cosine similarity weighted, 0–100)
- `α` — Adaptive weight parameter based on user interaction density

### Feature Signals Bonus

The content score `C_content` is no longer based solely on genre. It now includes a **Feature Signal Bonus**:

```text
C_content = GenreScore + min(SignalBonus, 30.0)
```

The bonus is summed from multiple signals and capped at 30 points to ensure genre preferences remain the primary driver.

| Signal | Models | Description | Weight |
| --- | --- | --- | --- |
| **Popularity** | Books | Based on `likedPercent` | 10.0 |
| **Author Affinity** | Books | Bonus for matching user's preferred authors | 12.0 |
| **Language Pref** | Books | Bonus for matching user's preferred language | 5.0 |
| **Recency** | TvMedia | Bonus for newer content (startyear) | 8.0 |
| **Media Type Match** | TvMedia | Bonus for matching user's movie vs show preference | 8.0 |

### Adaptive Alpha

α is computed dynamically based on the user's rating count:

```text
α = 1.0 - min(rating_count / threshold, 1.0) × cf_weight
```

- **New users** (few ratings): α ≈ 1.0 → mostly content-based recommendations
- **Active users** (many ratings): α = 1.0 − cf_weight → full hybrid blend
- **Default threshold**: 15 ratings, **default cf_weight**: 0.4

---

## Core Hybrid Logic (`myutils/recommendation.py`)

### `get_hybrid_recommendation(user, user_needed_genres, interaction_model, item_model, item_field, ...)`

- **Purpose:** Combines genre-based and collaborative filtering results into a single ranked list.
- **Key Parameters:**
  - `cf_weight`: Weight (0.0 to 1.0) for collaborative results. Default is `0.4`.
  - `rating_count`: When provided, enables adaptive α computation.
- **Exposed Functions:** This module also re-exports `get_content_based_recommendations` and `get_collaborative_recommendations` for convenience.

### `compute_adaptive_alpha(rating_count, cf_weight, threshold)`

- **Purpose:** Computes the content-based weight α that adapts to user rating density.
- **Returns:** α value in `[1.0 - cf_weight, 1.0]`.

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
  - `get_item_similarities`: Identifies items with high affinity to a target item. **Results are cached in Redis** (TTL: 6 hours) for performance.
  - `invalidate_similarity_cache`: Clears cached similarity data for a specific item. Called automatically when new ratings are saved.

---

## Cold-Start Strategies (`myutils/cold_start.py`)

### `get_popular_by_genre(item_model, genre_prefs, ...)`

- **Purpose:** Returns popular items filtered by a user's genre preferences.
- **Behavior:** New users with no ratings receive genre-weighted popularity results. If no genre preferences exist, global popularity is used as a fallback.

### `boost_new_items(recommendations, interaction_model, item_field, genre_prefs, item_model, ...)`

- **Purpose:** Boosts under-rated items that match the user's genre preferences.
- **Behavior:** Items with fewer than `min_ratings` (default: 5) user ratings receive a score bonus proportional to genre overlap, ensuring new content surfaces alongside established items.

---

## Evaluation Metrics (`myutils/evaluation.py`)

Offline recommendation quality measurement using standard IR metrics.

| Function | Description |
| --- | --- |
| `train_test_split(ratings, ratio, seed)` | Split user-item rating records into train/test sets |
| `precision_at_k(recommended, relevant, k)` | Fraction of top-K recommendations that are relevant |
| `recall_at_k(recommended, relevant, k)` | Fraction of relevant items found in top-K |
| `ndcg_at_k(recommended, relevant, k)` | Normalized Discounted Cumulative Gain at K |
| `evaluate_recommendations(user_recs, user_rel, k)` | Batch evaluation across all users |

### Running Evaluation

```sh
python manage.py evaluate_engine --k 10 --split 0.8 --seed 42
```

This command runs offline evaluation against existing rating data and prints Precision@K, Recall@K, and NDCG@K for both Books and TV Media.

---

## API Parameters

### Private Recommendation Endpoints

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `cf` | bool | `true` | Enable/disable collaborative filtering |
| `alpha` | float | `0.4` | Override cf_weight (0.0–1.0). Ignored when `cf=false` |

**Examples:**

```text
GET /api/books/recommend/private/?alpha=0.7     # More CF influence
GET /api/books/recommend/private/?alpha=0.1     # Mostly content-based
GET /api/books/recommend/private/?cf=false       # Pure content-based (alpha ignored)
```

---

## Usage Notes

- **Primary Entry Point**: Use `get_hybrid_recommendation` for personalized user dashboards.
- **Toggling CF**: The API views support a `cf=true/false` parameter to enable or disable the collaborative component.
- **Alpha Override**: The `alpha` parameter lets clients experiment with different hybrid weights.
- **Cold-Start**: New users automatically receive popularity-based recommendations. New items are boosted when they match user genre preferences.
- **Dependency**: All utilities require Django models and appropriate rating data to function effectively.
