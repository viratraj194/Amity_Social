# Current Task: list_posts Page & Components

## Objective
Develop and refine the `list_posts` page, including the post display and all related components (comments, likes, etc.).

## Project Map (Relevant to current task)
- **Posts App (`list_posts/`):**
    - `models.py`: `UserPosts`, `Like`, `Comment`, `Notification`, `UserSavedPosts`.
    - `views.py`: 
        - `list_posts`: Main feed (paginated via HTMX).
        - `add_posts`: Create posts (Image/Confession).
        - `add_comment`: AJAX comment/reply creation.
        - `get_comments`: AJAX fetch comments/replies.
        - `post_like`: AJAX toggle like.
        - `save_post`: AJAX toggle bookmark.
- **Templates (`templates/list_posts/`):**
    - `list_posts.html`: Main container, contains post creation modal, sidebar, and embedded AJAX logic for interactions.
    - `post.html`: Individual post component. Handles display and local interaction UI (like/comment/save buttons).
    - `loop_posts.html`: HTMX partial for infinite scroll/pagination.
- **Static Files:**
    - `static/js/js_for_list_post_page.js`: UI logic for Swiper, modals, and comment toggles.
    - `static/js/js_components_for_ajax.js`: Follow request logic and search visibility.
- **JavaScript Interactions (in `list_posts.html`):**
    - `$(document).on('click', '.like_post', ...)`: Handles likes.
    - `$(document).on('click', '.posts-save', ...)`: Handles bookmarks.
    - `$(document).on('click', '.add_comments', ...)`: Handles comment/reply submission.
    - `$(document).on('click', '.show-comments-btn', ...)`: Handles fetching comments.

## Current Sub-tasks
- [x] Research `list_posts` models and views.
- [x] Identify and map templates in `templates/list_posts/`.
- [x] Analyze `templates/list_posts/list_posts.html` and `post.html`.
- [x] Analyze `static/js/js_for_list_post_page.js`.
- [x] Map JavaScript event listeners for post interactions (likes, comments, bookmarks).
- [x] Fix UI flaws and accessibility issues in `PostContainers` modal.
    - [x] Add borders and placeholders to textareas/inputs.
    - [x] Implement "Empty State" box for Image Post mode.
    - [x] Create mobile-friendly wide "Upload Photo" button.
    - [x] Set dynamic height (min-height: 400px).
    - [x] Ensure Dark Mode consistency (Vircle theme).
- [ ] Wait for user instructions for specific modifications.

## Notes
- Infinite scroll is implemented via HTMX (`revealed` trigger in `loop_posts.html`).
- Likes, Saves, and Comments use jQuery AJAX with event delegation.
- Post creation supports "Image Post" and "Confession" modes.
