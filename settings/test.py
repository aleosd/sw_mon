from .settings import *

TEST_DISCOVER_PATTERN = "test_*"
TEST_RUNNER = 'django_test_exclude.runners.ExcludeTestSuiteRunner'
TEST_EXCLUDE = (
    'smart_selects',
    'django.contrib',
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    },
}

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    './templates',
)