"""
Module containing tests for the base scraper.
"""
# std lib imports

# third party imports
from requests.exceptions import HTTPError
import requests
import responses

# our imports
from .base import BaseTestCase
from .. import constants
from ..base_scraper import BaseScraper


class BaseScraperTests(BaseTestCase):
    """
    Tests the base scraper.
    """

    def setUp(self):
        """ Runs before each test. """
        super().setUp()
        self.client = BaseScraper()

    def test_session_used(self):
        """ Assert that a requests session is being used. """
        self.assertTrue(isinstance(self.client, requests.Session))

    def test_headers(self):
        """ Assert that the correct headers are being used. """
        self.assertEqual(self.client.headers, constants.HEADERS)

    def test_failed_responses(self):
        """ Assert that 4xx and 5xx responses raise exceptions. """

        # make certain urls return 400 and 500 status codes
        self.mock_responses.add(responses.GET, "https://200.com/", status=200)
        self.mock_responses.add(responses.GET, "https://400.com/", status=400)
        self.mock_responses.add(responses.GET, "https://500.com/", status=500)

        # assert that 200 status code does not raise exception
        self.client.get("https://200.com/")

        # assert that 4xx and 5xx status codes raise exception
        with self.assertRaises(HTTPError):
            self.client.get("https://400.com/")

        with self.assertRaises(HTTPError):
            self.client.get("https://500.com/")
