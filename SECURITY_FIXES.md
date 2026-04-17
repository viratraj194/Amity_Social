# Security Fixes and Improvements

This document summarizes all security improvements implemented in the Django project.

---


## PRIORITY 1 — CRITICAL (MUST FIX)

### 1. Rate Limiting

**Files Modified:**
- `accounts/views.py` - login (line 92), forgot_password (line 131)
- `list_posts/views.py` - add_comment (line 144), post_like (line 246)
- `amity_social_main/settings.py` - Added `ratelimit` to INSTALLED_APPS

**Implementation:**
```python
@ratelimit(key='ip', rate='5/m', block=True, method=['POST'])
def login(request):
    # 5 attempts per minute per IP

@ratelimit(key='ip', rate='3/h', block=True, method=['POST'])
def forgot_password(request):
    # 3 attempts per hour per IP

@ratelimit(key='user', rate='10/m', block=True, method=['POST'])
def add_comment(request, post_id):
    # 10 comments per minute per user

@ratelimit(key='user', rate='15/m', block=True, method=['POST'])
def post_like(request, post_id):
    # 15 likes per minute per user
```

---

### 2. File Upload Validation

**Files Modified:**
- `amity_social_main/validators.py` (NEW) - Validation functions
- `list_posts/forms.py` - addPostsForm validation
- `events/forms.py` - addEventsForm validation

**Implementation:**
- Max size: 2MB
- Allowed extensions: jpg, jpeg, png, webp
- Validators: `validate_file_size()`, `validate_file_extension()`, `validate_image_field()`

---

### 3. Pagination (MANDATORY)

**Already Implemented:**
- `list_posts/views.py` - list_posts: 15 items per page
- `events/views.py` - allEvents: 12 items per page
- `accounts/views.py` - UserDashboard, SavedPosts: 8 items per page

All views use Django's Paginator with proper page handling.

---

### 4. Debug Safety

**Files Modified:**
- `amity_social_main/settings.py`

**Changes:**
```python
DEBUG = config('DEBUG', default='False', cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')
```

**Environment Configuration:**
- `.env.example` created with all required environment variables
- DEBUG defaults to False in production

---

## PRIORITY 2 — SECURITY HARDENING

### 5. Redis Security

**Files Modified:**
- `amity_social_main/settings.py` - CHANNEL_LAYERS, CACHES
- `accounts/views.py` - redis_instance, get_user_status

**Changes:**
```python
# Channel Layers
"password": config('REDIS_PASSWORD', default=None),

# Cache
'LOCATION': f"redis://:{config('REDIS_PASSWORD', default='')}@{config('REDIS_HOST', default='127.0.0.1')}:{config('REDIS_PORT', default='6379')}/1"
```

---

### 6. Content Security Policy (CSP)

**Files Modified:**
- `amity_social_main/settings.py`

**Changes:**
```python
MIDDLEWARE = [
    # ...
    'csp.middleware.CSPMiddleware',
]

# CSP Headers
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", 'data:', 'blob:')
CSP_FONT_SRC = ("'self'", 'data:')
CSP_CONNECT_SRC = ("'self'", 'wss:', 'ws:')
CSP_OBJECT_SRC = ("'none'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
```

---

### 7. Permission System Cleanup

**Files Created:**
- `amity_social_main/decorators.py` (NEW)

**Reusable Decorators:**
- `@owner_required(model_class, lookup_field, lookup_url_kwarg, redirect_url)` - Check object ownership
- `@self_or_owner_required(redirect_url)` - Check if user is accessing own resource
- `@is_following_or_self(redirect_url)` - Check if user follows target

**Usage Example:**
```python
@owner_required(Event, lookup_url_kwarg='event_id')
def editEvent(request, event_id):
    # event object automatically checked for ownership
    ...
```

---

## PRIORITY 3 — PERFORMANCE OPTIMIZATION

### 8. Full Query Optimization

**All views now use:**
- `select_related()` for ForeignKey relationships
- `prefetch_related()` for ManyToMany/Reverse ForeignKey
- Pre-fetched sets for efficient lookups

**Examples:**
```python
# events/views.py
all_events = Event.objects.select_related('eventCreator').order_by('-created_at')

# list_posts/views.py
posts = UserPosts.objects.filter(...).select_related('user__userprofile')
comments = Comment.objects.filter(...).select_related('user__userprofile')
```

---

### 9. Caching

**Files Modified:**
- `amity_social_main/settings.py` - Cache configuration (60 second timeout)
- `events/views.py` - allEvents cached for 60 seconds
- `list_posts/views.py` - list_posts cached for 30 seconds

**Cache Invalidation:**
- Adding post → invalidates college feed cache
- Adding/editing/deleting event → invalidates event list cache
- Deleting post → invalidates college feed cache

**Configuration:**
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://:password@host:port/1',
        'TIMEOUT': 60,
    }
}
```

---

## Environment Variables Required

Create a `.env` file based on `.env.example`:

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Database
DB_NAME=amity_social
DB_USER=username
DB_PASSWORD=password
DB_HOST=localhost

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=app_password

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Security
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
```

---

## Dependencies to Install

```bash
pip install django-ratelimit django-csp python-decouple
```

---

## Summary

| Priority | Issue | Status |
|----------|-------|--------|
| P1 | Rate Limiting | ✅ Fixed |
| P1 | File Upload Validation | ✅ Fixed |
| P1 | Pagination | ✅ Verified |
| P1 | DEBUG Safety | ✅ Fixed |
| P2 | Redis Security | ✅ Fixed |
| P2 | CSP Headers | ✅ Fixed |
| P2 | Permission System | ✅ Fixed |
| P3 | Query Optimization | ✅ Fixed |
| P3 | Caching | ✅ Fixed |
