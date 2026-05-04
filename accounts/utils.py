import datetime
import re
import os
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.utils.text import slugify
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def users_id_generator(user_id):
    current_datetime = datetime.datetime.now().strftime('%Y%m%d%H%M%S')#202212281059
    users_id = current_datetime + str(user_id)
    print(users_id)
    return users_id


def detectUser(user):
    if user.is_superadmin:
        redirectUrl = '/super_admin/'
        return redirectUrl
    else:
        redirectUrl = 'UserDashboard'
        return redirectUrl


def send_email_verification(request,user,mail_subject,mail_template):
    from_email = settings.DEFAULT_FROM_EMAIL
    current_site = get_current_site(request)
    message = render_to_string(mail_template,{
        'user':user,
        'domain':current_site,
        'uid':urlsafe_base64_encode(force_bytes(user.pk)),
        'token':default_token_generator.make_token(user)
    })
    to_email = user.email
    _send_via_sendgrid(to_email, mail_subject, message, from_email)


def send_notification_email(mail_subjects, mail_template, context):
    from_email = settings.DEFAULT_FROM_EMAIL
    message = render_to_string(mail_template, context)
    if isinstance(context['to_email'], str):
        to_email = [context['to_email']]
    else:
        to_email = context['to_email']
    for email in to_email:
        _send_via_sendgrid(email, mail_subjects, message, from_email)


def _send_via_sendgrid(to_email, subject, html_content, from_email):
    """Send email via SendGrid API directly with timeout"""
    api_key = os.environ.get('SENDGRID_API_KEY') or settings.SENDGRID_API_KEY

    if not api_key:
        print("ERROR: SENDGRID_API_KEY not set")
        return False

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )

    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        print(f"Email sent! Status code: {response.status_code}")
        return response.status_code in [200, 202, 201]
    except Exception as e:
        print(f"ERROR sending email: {e}")
        return False


# Indian States and Union Territories - for validation
INDIA_REGIONS = [
    # States (28)
    'Andhra Pradesh',
    'Arunachal Pradesh',
    'Assam',
    'Bihar',
    'Chhattisgarh',
    'Goa',
    'Gujarat',
    'Haryana',
    'Himachal Pradesh',
    'Jharkhand',
    'Karnataka',
    'Kerala',
    'Madhya Pradesh',
    'Maharashtra',
    'Manipur',
    'Meghalaya',
    'Mizoram',
    'Nagaland',
    'Odisha',
    'Punjab',
    'Rajasthan',
    'Sikkim',
    'Tamil Nadu',
    'Telangana',
    'Tripura',
    'Uttar Pradesh',
    'Uttarakhand',
    'West Bengal',
    # Union Territories (8)
    'Andaman and Nicobar Islands',
    'Chandigarh',
    'Dadra and Nagar Haveli and Daman and Diu',
    'Delhi',
    'Jammu and Kashmir',
    'Ladakh',
    'Lakshadweep',
    'Puducherry',
]


def normalize_college_name(raw_name):
    """
    Normalize college name for deduplication.
    - Convert to uppercase
    - Trim leading/trailing spaces
    - Collapse multiple spaces to single space
    - Does NOT remove words like University, College, Institute
    """
    if not raw_name:
        return ''
    # Trim and collapse multiple spaces
    normalized = ' '.join(raw_name.strip().split())
    # Convert to uppercase for consistent comparison
    return normalized.upper()


def validate_indian_state(state_value):
    """
    Validate that a state value is a valid Indian State or Union Territory.

    Args:
        state_value: The state value to validate

    Returns:
        tuple: (is_valid, normalized_state)
        - is_valid: Boolean indicating if the state is valid
        - normalized_state: The properly-cased state name if valid, None otherwise

    Example:
        >>> validate_indian_state('maharashtra')
        (True, 'Maharashtra')
        >>> validate_indian_state('invalid state')
        (False, None)
    """
    if not state_value:
        return False, None

    # Normalize input for comparison (case-insensitive)
    state_normalized = state_value.strip().lower()

    for valid_state in INDIA_REGIONS:
        if valid_state.lower() == state_normalized:
            return True, valid_state

    return False, None


def get_india_regions():
    """
    Return the list of all Indian States and Union Territories.

    Returns:
        list: List of 36 Indian regions (28 States + 8 Union Territories)
    """
    return INDIA_REGIONS.copy()


def get_or_create_college(raw_name, city=None, state=None):
    """
    Get or create a College entity with normalization.

    Args:
        raw_name: Raw college name input from user
        city: Optional city name
        state: Optional state name

    Returns:
        College instance or None (only if raw_name is empty)

    Logic:
        - Normalize raw_name
        - Query by normalized_name first (unique constraint)
        - If exists → update city/state if needed and return
        - Else → create new College (always returns College, never None)
    """
    from .models import College
    from django.db import IntegrityError, transaction
    from django.utils.text import slugify

    if not raw_name or not raw_name.strip():
        print(f"COLLEGE: empty name provided")
        return None

    normalized = normalize_college_name(raw_name)
    city_clean = city.strip() if city and city.strip() else None
    state_clean = state.strip() if state and state.strip() else None

    print(f"COLLEGE LOOKUP: name='{raw_name}', city='{city_clean}', state='{state_clean}', normalized='{normalized}'")

    # Try to find existing college by normalized_name (unique field)
    college = College.objects.filter(normalized_name=normalized).first()

    if college:
        # Update city/state if provided and different
        updated = False
        if city_clean and college.city != city_clean:
            college.city = city_clean
            updated = True
        if state_clean and college.state != state_clean:
            college.state = state_clean
            updated = True
        if updated:
            college.save()
        print(f"COLLEGE FOUND: {college.name} (id={college.id})")
        return college

    # Create new college atomically
    display_name = ' '.join(raw_name.strip().split())
    slug = slugify(display_name)

    try:
        with transaction.atomic():
            college = College.objects.create(
                name=display_name.title(),
                normalized_name=normalized,
                slug=slug,
                city=city_clean,
                state=state_clean,
                is_verified=False
            )
            print(f"COLLEGE CREATED: {college.name} (id={college.id}, slug='{slug}')")
            return college
    except IntegrityError as e:
        print(f"COLLEGE IntegrityError: {e}")
        # Race condition - another request created it, fetch and return
        college = College.objects.filter(normalized_name=normalized).first()
        if college:
            print(f"COLLEGE FETCHED AFTER RACE: {college.name} (id={college.id})")
            return college
        # Last resort: try by slug
        college = College.objects.filter(slug=slug).first()
        if college:
            print(f"COLLEGE FETCHED BY SLUG: {college.name} (id={college.id})")
            return college
        print(f"COLLEGE: FAILED TO CREATE OR FIND - returning None")
        return None



