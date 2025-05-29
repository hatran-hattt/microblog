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
    loadingIndicator.classList.remove('hidden');

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
            endOfContent.classList.remove('hidden'); // Show end message
        }

    } catch (error) {
        console.error("Failed to fetch posts:", error);
        // Optionally display an error message to the user
    } finally {
        isLoading = false;
        loadingIndicator.classList.add('hidden');
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
    let url = `/api/posts?pagination_type=offset&per_page=${PER_PAGE}&page=${page}`;
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
function renderPagination(pagination_info, currentPage) {
    const paginationBar = document.getElementById('pagination-bar');
    paginationBar.classList.remove('hidden');
    if (!pagination_info || !pagination_info.total_page) {
        paginationBar.innerHTML = "";
        return;
    }
    let html = '<ul class="pagination">';
    for (let p = 1; p <= pagination_info.total_page; p++) {
        html += `<li${p === currentPage ? ' class="active"' : ''}>
            <a href="#" onclick="loadPosts_offset(${p}); return false;">${p}</a>
        </li>`;
    }
    html += '</ul>';
    paginationBar.innerHTML = html;
}
// ------OFFSET APPROACH-----End

// Function to create a post HTML element
function createPostElement(post) {
    const div = document.createElement('div');
    div.className = 'post';
    div.innerHTML = `
        <img
            src="${post.author.avatar_url}"
            alt="Post Author Avatar"
            class="post-avatar"
            width="50"
            height="50"
        />
        <div class="post-content">
            <p>
            <span class="author-name"
                ><a href="${post.author.user_url}"
                >${post.author.display_name}</a
                ></span
            >
            </p>
            <p class="post-timestamp">Posted at ${post.timestamp}</p>
            <p>${post.content}</p>
        </div>
    `;
    return div;
}