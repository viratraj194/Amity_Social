# 🔒 Pre-Production Security Audit Report
**Project:** Amity Social | **Scope:** Image Handling, Profile Updates, Cloudinary Integration  
**Audited:** `accounts/views.py`, `accounts/forms.py`, `accounts/models.py`, `validators.py`, `decorators.py`, `list_posts/views.py`, `list_posts/forms.py`, `settings.py`

---

## ✅ Passed Checks

| Check | Result |
|---|---|
| **IDOR** — `userProfileSettings` uses `request.user` | ✅ PASS — Profile is fetched via `get_object_or_404(UserProfile, user=request.user)`. No parameter tampering possible. |
| **SSRF / Arbitrary URL Injection** | ✅ PASS — App uses `request.FILES` and standard `ImageField`. No unvalidated URL strings accepted from the client. |

---

## 🚨 Issues Found

### [HIGH] — Unrestricted File Upload & Stored XSS via SVG Injection
**File:** [`accounts/forms.py`](file:///D:/projects/amity_social/accounts/forms.py) (Line 89)

**Exploitation Scenario:**  
`userProfileForm` explicitly overrides `profile_picture` and `cover_photo` as `forms.ImageField` but **does not attach** `validate_image_field` — the validator defined in `validators.py` that enforces the 2MB limit and allowed extensions. Unlike `addPostsForm` which uses it correctly, the profile form has no server-side size or extension enforcement. An attacker can:
- Upload an `.svg` file containing embedded `<script>` tags → **Stored XSS** executed in any browser rendering the image URL.
- Upload arbitrarily large files → **Storage abuse / DoS** on Cloudinary quota.

**Fix:**
```python
from amity_social_main.validators import validate_image_field

class userProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'btn btn-info'}),
        validators=[validate_image_field]   # ← ADD THIS
    )
    cover_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'btn btn-info'}),
        validators=[validate_image_field]   # ← ADD THIS
    )
```

---

### [HIGH] — Missing `transaction.atomic()` for Multi-Model Profile Updates
**File:** [`accounts/views.py`](file:///D:/projects/amity_social/accounts/views.py) (Line 252)

**Exploitation Scenario:**  
In `userProfileSettings`, the view calls `user_profile_form.save()`, then runs college lookup logic, then calls `user.save()`. If the second `user.save()` fails (DB constraint, timeout, etc.), the profile model is already mutated in the DB while the user record is not — leaving **corrupted partial state** with no rollback.

**Fix:**
```python
from django.db import transaction

if user_profile_form.is_valid() and user_info_form.is_valid():
    try:
        with transaction.atomic():
            user_profile_form.save()

            old_college_id = user.college.id if user.college else None
            state = user_info_form.cleaned_data.get('state')
            city = user_info_form.cleaned_data.get('city')
            college_name = (
                request.POST.get('college_name', '').strip()
                or request.POST.get('college_name_hidden', '').strip()
            )

            if state: user.state = state
            if city: user.city = city

            new_college_id = None
            if college_name and state and city:
                college = get_or_create_college(college_name, city=city, state=state)
                if not college:
                    college = College.objects.filter(name__iexact=college_name.strip()).first()
                if college:
                    user.college = college
                    new_college_id = college.id

            user.first_name = user_info_form.cleaned_data['first_name']
            user.last_name  = user_info_form.cleaned_data['last_name']
            user.username   = user_info_form.cleaned_data['username']
            user.phone_number = user_info_form.cleaned_data['phone_number']
            user.save()

        # Cache invalidation OUTSIDE atomic block
        if old_college_id:
            cache.delete(f'posts_list_{request.user.id}_{old_college_id}_page_1')
        if new_college_id:
            cache.delete(f'posts_list_{request.user.id}_{new_college_id}_page_1')

        messages.success(request, 'Profile updated successfully.')
    except Exception as e:
        messages.error(request, 'An error occurred while updating your profile. Please try again.')
```

---

### [MEDIUM] — Image Clearing Regression (Form Validation Bug)
**File:** [`accounts/forms.py`](file:///D:/projects/amity_social/accounts/forms.py) (Line 89)

**Exploitation Scenario:**  
`forms.ImageField` defaults to `required=True`. If a user updates their bio or name *without* re-uploading an image, the form will **fail validation silently** — the user gets no update and no clear error. Additionally, since `ClearableFileInput` is not used, the user has no way to remove an existing image.

**Fix:**  
Already covered by the HIGH fix above — ensuring both fields have `required=False` resolves this.

---

### [MEDIUM] — Unhandled Cloudinary Upload Exception → 500 Error
**File:** [`list_posts/views.py`](file:///D:/projects/amity_social/list_posts/views.py) (Line 117)

**Exploitation Scenario:**  
`post.save()` in `add_posts()` makes a synchronous Cloudinary API call. If Cloudinary is down, rate-limits the app, or times out, Django raises an unhandled exception → **500 Internal Server Error** exposed to the user.

**Fix:**
```python
try:
    post.save()
    user_name = f'{request.user.first_name}{request.user.last_name}'
    post.post_slug = slugify(user_name) + '_' + str(post.id)
    post.save()
    college_id = request.user.college.id if request.user.college else None
    cache.delete(f'posts_list_{request.user.id}_{college_id}_page_1')
    messages.success(request, 'New post is added.')
except Exception:
    messages.error(request, 'Failed to upload image. Please try again later.')
```

---

## Summary

| # | Severity | Issue | File | Status |
|---|---|---|---|---|
| 1 | 🔴 HIGH | SVG/Unrestricted Upload — missing `validate_image_field` on profile form | `accounts/forms.py:89` | ⚠️ Fix Required |
| 2 | 🔴 HIGH | No `transaction.atomic()` — partial DB state on profile save failure | `accounts/views.py:252` | ⚠️ Fix Required |
| 3 | 🟡 MEDIUM | Image field `required=True` regression — form fails without re-upload | `accounts/forms.py:89` | ⚠️ Fix Required |
| 4 | 🟡 MEDIUM | Unhandled Cloudinary exception in `add_posts` → 500 error | `list_posts/views.py:117` | ⚠️ Fix Required |
| 5 | ✅ PASS | IDOR — profile tied to `request.user` | `accounts/views.py` | Safe |
| 6 | ✅ PASS | SSRF — no client-supplied URLs accepted | `accounts/views.py` | Safe |

> [!CAUTION]
> The two HIGH severity issues should be resolved **before** pushing to the live branch. The SVG injection vector in particular could result in Stored XSS for any user viewing an affected profile.
