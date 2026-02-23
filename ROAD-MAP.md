# RecAnthology Strategic Roadmap

## The Vision

RecAnthology (Recommended Anthology) is an intelligent, extensible recommendation platform designed to redefine how users discover and curate collections of books, movies, and TV shows.

This project serves as:

- A modular backend system design exercise
- A practical implementation of hybrid recommender systems
- A research-informed, evaluation-driven open-source platform

The objective is architectural clarity, algorithmic rigor, and measurable recommendation quality — not infrastructure maximalism.

---

## Core Pillars

### 1. Intelligent Discovery

A formally defined **Hybrid Recommendation Engine**:

**Formula:**
&nbsp;&nbsp;&nbsp;&nbsp;<code>FinalScore = α · C<sub>content</sub> + (1 - α) · C<sub>cf</sub></code>

Where:

- `C_content` — content-based score (normalized genre affinity)
- `C_cf` — collaborative filtering score (cosine similarity between items)
- `α` — weight parameter adapting to user interaction count/density

Features:

- Cold-start fallback strategies
- Score normalization (0–100)
- Popularity bias dampening
- Configurable hybrid weighting

---

### 2. Extensible Architecture

A modular Django/DRF backend featuring:

- Pluggable recommendation strategies
- Clean service-layer abstraction
- Separation of scoring, ranking, and explanation layers
- Evaluation and metrics as first-class modules
- Config-driven algorithm parameters

---

### 3. Measurable Performance & Evaluation

Recommendation quality is validated using offline evaluation metrics:

- Precision@K
- Recall@K
- NDCG
- Coverage
- Diversity

Development performance targets:

- P95 recommendation latency < 200ms (local benchmark)
- Cache hit ratio > 70%
- Deterministic scoring across test seeds

---

## The Milestone Map

---

### Milestone 1: The Unified Base (Completed)

- [x] Multi-media core models (Books, Movies, TV)
- [x] JWT-based stateless authentication
- [x] Hybrid Engine v1 (Content + Item-Item CF)
- [x] API standardization via shared mixins
- [x] Redis caching layer integration

**Deliverable:**
Functional hybrid recommender with modular architecture.

---

### Milestone 2: Algorithmic Maturity & Evaluation (Completed)

**Focus:** Make the engine technically defensible and measurable.

- [x] Formal hybrid scoring equation documented and configurable
- [x] Adaptive `cf_weight` based on rating density
- [x] Cold-start strategy:
  - New users → genre-weighted popularity
  - New items → genre-affinity boosting
- [x] Evaluation module:
  - Offline train/test split
  - Precision@K
  - Recall@K
  - NDCG
- [x] Similarity matrix persistence (precomputed + cached)
- [x] Similarity Shrinkage (λ-regularization for sparse data)
- [x] Candidate Pool Limiting (Signal-to-noise optimization)
- [x] Feature signals (Multi-signal metadata scoring)
- [x] Comprehensive test coverage for scoring logic
- [x] API parameterization (`?cf=true&alpha=0.6`)
- [x] Evaluation Baselines (Popularity vs Content vs Hybrid)

**Deliverable:**
A benchmarked, evaluation-driven hybrid recommender.

---

### Milestone 3: Interpretability & Data Expansion

**Focus:** Increase sophistication without infrastructure overreach.

- [ ] Explainable AI layer:
  - Score decomposition
  - Structured “Why this was recommended” response field
- [ ] External metadata ingestion:
  - TMDb
  - OpenLibrary
  - IMDb datasets (where permitted)
- [ ] Metadata normalization & deduplication pipeline
- [ ] Basic rate-limit handling and ingestion scheduling
- [ ] Small reproducible benchmark dataset for evaluation

**Deliverable:**
Transparent, data-enriched recommendation system with reproducible experiments.

---

### Milestone 4: Product Evolution & Visualization

**Focus:** User insight and interface modernization.

- [ ] React/Next.js frontend (headless API consumption)
- [ ] User taste visualization dashboard:
  - Genre affinity radar chart
  - Rating distribution histogram
- [ ] Time-decay weighting for recency-aware scoring
- [ ] Trending signal integration (optional hybrid feature boost)
- [ ] Basic A/B testing toggle for hybrid weight experimentation

**Deliverable:**
A modern interface showcasing user preference modeling and algorithm experimentation.

---

**Document Version:** 2.0.0
**Last Updated:** February 2026
