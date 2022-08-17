"""
Module containing django config values for testing.
"""
# pylint: disable=wildcard-import, unused-wildcard-import
from .settings import *  # noqa: F401,F403


# for tests, set logging to the default django config
# so that tests arent noisy
LOGGING = {
    'version': 1,                       # the dictConfig format version
    'disable_existing_loggers': False,  # retain the default loggers
}
