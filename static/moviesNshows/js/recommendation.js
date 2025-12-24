// Get vars provided in @templates/moviesNshows/recommendation.html
// We expect these to be available as global vars injected by Django template context:
// - window.RECOMMENDATION_VARS = {
//   userGenrePreferencesUrl: ...,
//   recommendPrivateUrl: ...,
//   mediaUrl: ...,
//   pageSize: ... (optional)
// }

const PAGE_SIZE = (window.RECOMMENDATION_VARS?.pageSize) ? parseInt(window.RECOMMENDATION_VARS.pageSize) : 20;
let recommendationsData = [];
let currentPage = 1;
let totalPages = 1;

function fetchTopGenres() {
    fetch(window.RECOMMENDATION_VARS.userGenrePreferencesUrl, {
        credentials: "same-origin",
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json"
        }
    })
    .then(resp => resp.json())
    .then(data => {
        const container = document.getElementById('top-genres-list');
        const loading = document.getElementById('top-genres-loading');
        loading.style.display = 'none';
        container.style.display = 'block';

        let genres = Array.isArray(data.tvmedia_genre_preferences) ? data.tvmedia_genre_preferences : [];
        genres = genres
            .filter(g => typeof g.preference === "number");

        // Split genres into loved (preference > 0) and hated (preference < 0)
        let loved = genres.filter(g => g.preference > 0).sort((a, b) => b.preference - a.preference);
        let hated = genres.filter(g => g.preference < 0).sort((a, b) => a.preference - b.preference);

        if (genres.length === 0) {
            container.innerHTML = `
                <div class="text-muted text-center py-3">
                    No genre preferences found yet.<br>
                    <span class="small">After you rate some movies or shows, your favorite genres will show up here!</span>
                </div>`;
            return;
        }

        let html = '';

        // Loved genres section
        html += `<div class="mb-3">`;
        html += `<div class="fw-bold text-success mb-2"><i class="bi bi-heart-fill"></i> Loved Genres</div>`;
        if (loved.length === 0) {
            html += `<div class="text-muted small mb-2">No favorite genres yet.</div>`;
        } else {
            html += `<div class="row justify-content-center gy-2 gx-2">`;
            loved.slice(0, 6).forEach((genre, idx) => {
                const genreName = genre.genre
                    ? genre.genre.charAt(0).toUpperCase() + genre.genre.slice(1)
                    : "Unknown";
                let prefVal = genre.preference;
                let prefClass = "";
                let icon = "";

                if (prefVal > 1.5) {
                    prefClass = "text-success";
                    icon = '<i class="bi bi-arrow-up-circle-fill me-1"></i>';
                } else if (prefVal > 0.5) {
                    prefClass = "text-primary";
                    icon = '<i class="bi bi-caret-up-fill me-1"></i>';
                } else {
                    prefClass = "text-info";
                    icon = '<i class="bi bi-bar-chart me-1"></i>';
                }

                html += `
                    <div class="col-6 col-sm-4 col-lg-3 d-flex align-items-stretch justify-content-center">
                        <span class="badge rounded-pill bg-light border border-1 ${prefClass} d-flex align-items-center px-3 py-2 fs-6 w-100 justify-content-center"
                              title="Score: +${prefVal.toFixed(2)}">
                            ${icon}
                            <span class="mx-1 fw-semibold">${genreName}</span>
                            <span class="ms-1 small">+${prefVal.toFixed(1)}</span>
                        </span>
                    </div>
                `;
            });
            html += `</div>`;
        }
        html += `</div>`;

        // Hated/Disliked genres section (only show if any exist)
        if (hated.length > 0) {
            html += `<div class="mb-2">`;
            html += `<div class="fw-bold text-danger mb-2"><i class="bi bi-emoji-angry"></i> Disliked Genres</div>`;
            html += `<div class="row justify-content-center gy-2 gx-2">`;
            hated.slice(0, 6).forEach((genre, idx) => {
                const genreName = genre.genre
                    ? genre.genre.charAt(0).toUpperCase() + genre.genre.slice(1)
                    : "Unknown";
                let prefVal = genre.preference;
                let prefClass = "";
                let icon = "";

                if (prefVal < -2) {
                    prefClass = "text-danger";
                    icon = '<i class="bi bi-arrow-down-circle-fill me-1"></i>';
                } else if (prefVal < -0.5) {
                    prefClass = "text-warning";
                    icon = '<i class="bi bi-caret-down-fill me-1"></i>';
                } else {
                    prefClass = "text-secondary";
                    icon = '<i class="bi bi-dash-circle me-1"></i>';
                }

                html += `
                    <div class="col-6 col-sm-4 col-lg-3 d-flex align-items-stretch justify-content-center">
                        <span class="badge rounded-pill bg-light border border-1 ${prefClass} d-flex align-items-center px-3 py-2 fs-6 w-100 justify-content-center"
                              title="Score: ${prefVal.toFixed(2)}">
                            ${icon}
                            <span class="mx-1 fw-semibold">${genreName}</span>
                            <span class="ms-1 small">${prefVal.toFixed(1)}</span>
                        </span>
                    </div>
                `;
            });
            html += `</div>`;
            html += `<div class="mt-2 small text-muted text-center">
                        <i class="bi bi-info-circle"></i>
                        <span>Your least favorite genres (these are less likely to be recommended).</span>
                    </div>`;
            html += `</div>`;
        }

        // Neutral zero values
        const neutral = genres.filter(g => g.preference === 0);
        if (neutral.length > 0) {
            html += `<div class="mb-2">`;
            html += `<div class="fw-bold text-secondary mb-2"><i class="bi bi-circle"></i> Neutral Genres</div>`;
            html += `<div class="row justify-content-center gy-2 gx-2">`;
            neutral.slice(0, 4).forEach((genre, idx) => {
                const genreName = genre.genre
                    ? genre.genre.charAt(0).toUpperCase() + genre.genre.slice(1)
                    : "Unknown";
                html += `
                    <div class="col-6 col-sm-4 col-lg-3 d-flex align-items-stretch justify-content-center">
                        <span class="badge rounded-pill bg-light border border-1 text-secondary d-flex align-items-center px-3 py-2 fs-6 w-100 justify-content-center"
                              title="Score: 0.00">
                            <i class="bi bi-dash-circle me-1"></i>
                            <span class="mx-1 fw-semibold">${genreName}</span>
                            <span class="ms-1 small">0.0</span>
                        </span>
                    </div>
                `;
            });
            html += `</div>`;
            html += `</div>`;
        }

        html += `
            <div class="mt-3 small text-muted text-center">
                <i class="bi bi-info-circle"></i>
                <span>Genres you love (more recommendations), dislike (less), or are neutral on.</span>
            </div>
        `;
        container.innerHTML = html;
        loading.innerHTML  = ""
    })
    .catch(() => {
        const loading = document.getElementById('top-genres-loading');
        loading.innerHTML = `<span class="text-danger"><i class="bi bi-x-circle"></i> Failed to load genres.</span>`;
    });
}


// Loads recommendations from API and triggers display of paginated results
function fetchRecommendations(page=1) {
    // Show loading
    const container = document.getElementById('recommendations-list');
    const loading = document.getElementById('recommendations-loading');
    const pagination = document.getElementById('recommendations-pagination');
    loading.style.display = '';
    container.style.display = 'none';
    pagination.innerHTML = '';
    container.innerHTML = '';

    // Only fetch first page, but all data, then paginate client-side
    fetch(window.RECOMMENDATION_VARS.recommendPrivateUrl, {
        credentials: 'same-origin',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json',
        }
    })
    .then(resp => resp.json())
    .then(data => {
        // Flatten the API data to an array
        const recs = (data.data && Array.isArray(data.data))
            ? Object.values(data.data)
            : Object.values(data.data || {});

        recommendationsData = recs;
        totalPages = Math.ceil(recommendationsData.length / PAGE_SIZE) || 1;
        displayRecommendationsPage(page);
    })
    .catch(() => {
        loading.style.display = '';
        loading.innerHTML = `<span class="text-danger"><i class="bi bi-x-circle"></i> Failed to load recommendations.</span>`;
        recommendationsData = [];
        totalPages = 1;
    });
}

function displayRecommendationsPage(page=1) {
    const container = document.getElementById('recommendations-list');
    const loading = document.getElementById('recommendations-loading');
    const pagination = document.getElementById('recommendations-pagination');
    loading.style.display = 'none';
    container.style.display = 'block';
    pagination.innerHTML = '';

    currentPage = Math.max(1, Math.min(page, totalPages));

    if (!recommendationsData || recommendationsData.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="bi bi-emoji-neutral" style="font-size: 2rem;"></i>
                <div>No personalized recommendations available.<br><span class="small">Please rate more TV and movies!</span></div>
            </div>`;
        pagination.innerHTML = "";
        return;
    }

    // Determine the page slice
    const startIdx = (currentPage - 1) * PAGE_SIZE;
    const endIdx = startIdx + PAGE_SIZE;
    const recs = recommendationsData.slice(startIdx, endIdx);

    // Responsive grid: 1 on sm, 2 on md, 3 on lg, 4 on xl+
    let html = `<div class="row row-cols-1 row-cols-sm-2 row-cols-lg-3 row-cols-xl-4 gy-4 gx-3 justify-content-center">`;
    recs.forEach((rec, idx) => {
        const media = rec.media || {};
        let coverImg = `${window.RECOMMENDATION_VARS.mediaUrl}moviesNshows/default_cover.jpg`;
        if (media.cover_image && media.cover_image.url) {
            coverImg = media.cover_image.url;
        }
        html += `
        <div class="col d-flex">
            <div class="card h-100 border-0 shadow-sm w-100 animate__animated animate__fadeIn" style="animation-delay:${idx*0.10}s">
                <div class="ratio ratio-16x9 recommend-cover-wrap">
                    <img src="${coverImg}" alt="${media.original_title ? media.original_title + ' Cover' : 'Media Cover'}"
                        onerror="this.onerror=null;this.src='${window.RECOMMENDATION_VARS.mediaUrl}moviesNshows/default_cover.jpg';"
                        class="card-img-top object-fit-cover rounded-top" style="min-height:135px; max-height:260px;">
                </div>
                <br>
                <div class="card-body d-flex flex-column pb-2 pt-3 px-3">
                    <h5 class="card-title mb-1 text-truncate" style="max-width: 90%;">
                        ${media.original_title || "&mdash;"}
                        ${media.startyear ? `<span class="small text-muted">(${media.startyear})</span>` : ""}
                    </h5>
                    <div class="d-flex flex-wrap align-items-center mb-2 gap-2">
                        <span class="badge bg-secondary small">${(media.media_type||"").charAt(0).toUpperCase() + (media.media_type||"").slice(1)}</span>
                        ${media.length ? `<span class="text-muted small d-flex align-items-center"><i class="bi bi-clock-history me-1"></i> ${media.length} min</span>` : ""}
                        ${media.over18 ? `<span class="badge bg-danger small ms-1">18+</span>` : ""}
                    </div>
                    <div class="mb-2">
                        ${(media.genre||[]).slice(0,4).map(g => `<span class="badge bg-light text-dark border me-1 mb-1 small">${g}</span>`).join('')}
                    </div>
                    ${rec.relativity !== undefined && rec.relativity !== null ? `
                    <div class="mt-auto">
                        <span class="text-success fw-bold small d-inline-flex align-items-center" title="Match score to your taste">
                            <i class="bi bi-graph-up"></i> Taste Score: <span class="ms-1">${Math.round(rec.relativity)}%</span>
                        </span>
                    </div>` : ""}
                </div>
            </div>
        </div>`;
    });
    html += "</div>";
    container.innerHTML = html;
    renderRecommendationsPagination();
}

function renderRecommendationsPagination() {
    const pagination = document.getElementById('recommendations-pagination');
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    let html = '';

    // Previous
    html += `<li class="page-item${currentPage <= 1 ? ' disabled' : ''}">
        <a class="page-link" href="#" tabindex="-1" aria-label="Previous" onclick="gotoRecommendationsPage(${currentPage-1});return false;">
            <span aria-hidden="true">&laquo;</span>
        </a>
    </li>`;

    // Numeric pages (show at most 5, centered on currentPage)
    let start = Math.max(1, currentPage - 2);
    let end = Math.min(totalPages, currentPage + 2);
    if (totalPages >= 5) {
        if (currentPage <= 3) {
            start = 1; end = 5;
        } else if (currentPage >= totalPages - 2) {
            start = totalPages - 4; end = totalPages;
        }
    }
    for (let i = start; i <= end; i++) {
        html += `<li class="page-item${i === currentPage ? ' active' : ''}">
            <a class="page-link" href="#" onclick="gotoRecommendationsPage(${i});return false;">${i}</a>
        </li>`;
    }

    // Next
    html += `<li class="page-item${currentPage >= totalPages ? ' disabled' : ''}">
        <a class="page-link" href="#" tabindex="-1" aria-label="Next" onclick="gotoRecommendationsPage(${currentPage+1});return false;">
            <span aria-hidden="true">&raquo;</span>
        </a>
    </li>`;
    pagination.innerHTML = html;
}

function gotoRecommendationsPage(page) {
    if (page < 1 || page > totalPages) return;
    displayRecommendationsPage(page);
}

document.addEventListener('DOMContentLoaded', function() {
    fetchTopGenres();
    fetchRecommendations(1);
});
