import sys

from .base import *

# like on dev
DEBUG = True

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        # https://stackoverflow.com/a/76117900
        # "disables the caching behavior for the tests, for static files to load properly"
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"
    },
}

# this is used to quelch a
# "UserWarning: No directory at: .../staticfiles/" warning
WHITENOISE_AUTOREFRESH = True

# don't email Jessica during testing!!
# don't email Jessica during testing!!
# don't email Jessica during testing!!
ENABLE_EMAILING_JESSICA_ON_EVENT_SUBMISSION = False

# set a custom TEST.NAME as the current one, test_nycnoise, extremely annoyingly,
# is not deletable as another session is using it.
# I'm very annoyed at this solution, and at the fact that I can't get
# to delete that database (and also don't know how it happened/how to avoid
# this from happening again). this is of course a temporary patch...
DATABASES["default"]["TEST"] = {
    "NAME": "test_nycnoise_tmp_name",
}
