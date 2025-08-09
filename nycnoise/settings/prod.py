from .base import *

DEBUG = False

# default logging doesn't log to console with DEBUG=False
# see https://github.com/django/django/blob/main/django/utils/log.py
# override i.e. always log to console
LOGGING["handlers"]["console"] = {
    "class": "logging.StreamHandler",
}

# add a custom TEST.NAME to the prod database
# as the current one, test_nycnoise, extremely annoyingly,
# is not deletable as another session is using it.
# I'm very annoyed at this solution, and at the fact that I can't get
# to delete that database (and also don't know how it happened/how to avoid
# this from happening again). this is of course a temporary patch...

DATABASES["default"]["TEST"] = {
    "NAME": "test_nycnoise_prod",
}
