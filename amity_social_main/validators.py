from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _
import os

# Maximum file size: 2MB
MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2MB

# Allowed extensions
ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']


def validate_file_size(value):
    """Validate that uploaded file does not exceed 2MB."""
    filesize = value.size
    if filesize > MAX_UPLOAD_SIZE:
        raise ValidationError(
            _('The maximum file size allowed is %(max_size)s. Current size is %(current_size)s.')
            % {
                'max_size': filesizeformat(MAX_UPLOAD_SIZE),
                'current_size': filesizeformat(filesize)
            }
        )


def validate_file_extension(value):
    """Validate that uploaded file has allowed extension (jpg, jpeg, png, webp)."""
    ext = os.path.splitext(value.name)[1][1:].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            _('File extension %(extension)s is not allowed. Allowed extensions are: %(allowed)s.')
            % {
                'extension': ext,
                'allowed': ', '.join(ALLOWED_EXTENSIONS)
            }
        )


def validate_image_field(value):
    """Combined validator for image fields - checks both size and extension."""
    validate_file_size(value)
    validate_file_extension(value)
