"""
Module containing base class for scrapers.
"""
# std lib imports

# third party imports
import requests

# our imports
from . import constants


class BaseScraper(requests.Session):
    """
    Base class that scrapers should inherit
    to properly configure their settings.
    """

    def __init__(self):
        super().__init__()
        self.headers.update(constants.HEADERS)

    def request(self, method, url, *args, **kwargs):
        """
        Override requests.Session.request to always raise
        exception on 4xx and 5xx responses.
        """
        resp = super().request(method, url, *args, **kwargs)
        resp.raise_for_status()
        return resp
