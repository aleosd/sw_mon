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
