import os
from dotenv import load_dotenv

load_dotenv()

env = os.getenv("DJANGO_ENV", "development")

if env == "production":
    from .production import *  # noqa: F403
else:
    from .development import *  # noqa: F403
