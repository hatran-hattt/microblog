// --- Initial Load ---
document.addEventListener("DOMContentLoaded", function () {
    if (PAGINATION_TYPE == "keyset") {
        loadPosts_keyset()
    } else {
        loadPosts_offset(1)
    }
    
});

// ------KEYSET APPROACH-----Start
const postsList = document.getElementById('posts-list');
const loadingIndicator = document.getElementById('loading-indicator');
const endOfContent = document.getElementById('end-of-content');

let nextCursor = null; // Stores the cursor for the next API call
let hasMore = true;    // Flag to know if there's more data to load
let isLoading = false; // Flag to prevent multiple concurrent requests

// Function to fetch posts from the API
async function loadPosts_keyset() {
    if (!hasMore || isLoading) {
        return; // Don't fetch if no more data or already loading
    }

    isLoading = true;
    loadingIndicator.classList.remove('d-none');

    let url = `/api/posts?search_condition=${SEARCH_CONDITION}&pagination_type=keyset&per_page=${PER_PAGE}`;
    if (USER_ID) {
        url += `&user_id=${USER_ID}`
    }
    if (nextCursor) {
        url += `&cursor_timestamp=${encodeURIComponent(nextCursor.cursor_timestamp)}`;
        url += `&cursor_id=${nextCursor.cursor_id}`;
    }

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        data.posts.forEach(post => {
            postsList.appendChild(createPostElement(post));
        });

        nextCursor = data.pagination_info.next_cursor; // Update cursor for next request
        hasMore = data.pagination_info.has_more;      // Update hasMore flag

        if (!hasMore) {
            endOfContent.classList.remove('d-none'); // Show end message
        }

    } catch (error) {
        console.error("Failed to fetch posts:", error);
        // Optionally display an error message to the user
    } finally {
        isLoading = false;
        loadingIndicator.classList.add('d-none');
    }
}

if (PAGINATION_TYPE == "keyset") {
    // --- Scroll Event Listener ---
    // Debouncing the scroll event to prevent excessive calls
    let scrollTimeout;
    window.addEventListener('scroll', () => {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            // Check if user is near the bottom of the page
            const scrollHeight = document.documentElement.scrollHeight;
            const scrollTop = document.documentElement.scrollTop;
            const clientHeight = document.documentElement.clientHeight;

            // Load more when user is within 200px from the bottom
            if (scrollTop + clientHeight >= scrollHeight - 200) {
                loadPosts_keyset();
            }
        }, 100); // Debounce time in ms
    });
}

// ------KEYSET APPROACH-----End


// ------OFFSET APPROACH-----Start
function loadPosts_offset(page) {
    let url = `/api/posts?search_condition=${SEARCH_CONDITION}&pagination_type=offset&per_page=${PER_PAGE}&page=${page}`;
    if (USER_ID) {
        url += `&user_id=${USER_ID}`
    }

    fetch(url)
        .then(response => response.json())
        .then(data => {
            postsList.innerHTML = "";
            data.posts.forEach(post => {
                postsList.appendChild(createPostElement(post));
            });
            renderPagination(data.pagination_info, page);
        });
}
function renderPagination(pagination_info, current_page) {
    const paginationBar = document.getElementById('pagination-bar');
    paginationBar.classList.remove('hidden');
    if (!pagination_info || !pagination_info.total_pages) {
        paginationBar.innerHTML = "";
        return;
    }

    // Pagination infos
    let total_pages = pagination_info.total_pages;
    let has_prev = current_page > 1
    let has_next = current_page < total_pages

    // Determine the start and end of the visible page range
    const pages_to_show = 4;
    let start_page = current_page - (pages_to_show / 2)
    let end_page = start_page + pages_to_show - 1

    // Adjust start_page if it goes below 1 
    if (start_page < 1) {
        start_page = 1
        end_page = pages_to_show // Ensure we still show 4 pages if possible
    }

    // Adjust end_page if it exceeds total_pages
    if (end_page > total_pages) {
        end_page = total_pages
        start_page = total_pages - pages_to_show + 1 // Adjust start_page to keep 4 pages if possible
        // Handle case where total pages < pages_to_show
        if (start_page < 1) {
            start_page = 1
        }
    }

    let prevOnclick = `onclick="loadPosts_offset(${current_page - 1}); return false;"`;
    let nextOnclick = `onclick="loadPosts_offset(${current_page + 1}); return false;"`;
    let html = `<ul class="pagination justify-content-center">
                    <li class="page-item ${has_prev ? '' : ' disabled'}">
                        <a class="page-link" href="#" tabindex="-1" 
                            ${has_prev ? prevOnclick : ' aria-disabled="true"'}>Previous</a>
                    </li>`;
    for (let p = start_page; p <= end_page; p++) {
        html += `<li class="page-item ${p === current_page ? ' active' : ''}">
            <a class="page-link" href="#" onclick="loadPosts_offset(${p}); return false;">${p}</a>
        </li>`;
    }
    html += `<li class="page-item ${has_next ? '' : ' disabled'}">
                <a class="page-link" href="#"
                    ${has_next ? nextOnclick : ' aria-disabled="true"'}>Next</a>
            </li>
        </ul>`;
    paginationBar.innerHTML = html;
}
// ------OFFSET APPROACH-----End

// Function to create a post HTML element
function createPostElement(post) {
    const div = document.createElement('div');
    div.className = 'post';
    div.innerHTML = `
        <div class="card p-3 mb-1">
        <div class="row g-0 align-items-start">
            <div class="col-auto">
                <img src="${post.author.avatar_url}" 
                    alt="Post Author Avatar" 
                    class="rounded-circle me-3 mt-1"
                    width="50" height="50">
            </div>
            <div class="col">
                <div class="card-body p-0">
                    <h6 class="mb-0">
                        <span class="fw-bold">
                            <a href="${post.author.user_url}" class="text-decoration-none text-primary">${post.author.display_name}</a>
                        </span>
                    </h6>
                    <p class="text-muted small mb-1">
                        Posted at ${(new Date(post.timestamp)).toLocaleString()}
                    </p>
                    <p class="mb-0">${post.content}</p>
                </div>
            </div>
        </div>
    </div>
    `
    return div;
}