import os
import dj_database_url
from .base import *  # noqa

DEBUG = False
ALLOWED_HOSTS = [host.strip() for host in os.environ.get("ALLOWED_HOSTS", "").split(",") if host.strip()]

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ["DATABASE_URL"],
        conn_max_age=600,
        ssl_require=True,
    )
}

SECURE_SSL_REDIRECT            = True
SECURE_HSTS_SECONDS            = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD            = True
SESSION_COOKIE_SECURE          = True
CSRF_COOKIE_SECURE             = True
SECURE_CONTENT_TYPE_NOSNIFF    = True
X_FRAME_OPTIONS                = "DENY"
SECURE_REFERRER_POLICY         = "strict-origin-when-cross-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")