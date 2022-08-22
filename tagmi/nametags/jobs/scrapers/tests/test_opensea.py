"""
Module containing tests for the opensea.py scraper.
"""
# std lib imports
from pathlib import Path

# third party imports
from responses.registries import OrderedRegistry
import responses

# our imports
from .base import BaseScraperTestCase
from .. import opensea
from ..base_scraper import BaseScraper
from ....models import Tag


class OpenseaTests(BaseScraperTestCase):
    """
    Tests the opensea scraper.
    """

    def setUp(self):
        """ Runs before each test. """

        super().setUp()
        self.client = opensea.OpenseaScraper()
        self.samples_dir = Path(self.samples_dir, "opensea")

    def _mock_landing_page_resp(self):
        """
        Register and return mock GET response for opensea landing page.
        """
        return self.mock_responses.add(
            responses.GET, "https://opensea.io/"
        )

    def _mock_profile_found_page_resp(self, address):
        """
        Register and return mock GET response for
        a valid opensea profile page.
        """
        filepath = Path(self.samples_dir, "profile_found.html")
        with open(filepath, "r", encoding="utf-8") as fobj:
            html_content = fobj.read()

            return self.mock_responses.add(
                responses.GET,
                f"https://opensea.io/{address}",
                body=html_content
            )

    def _mock_profile_not_found_page_resp(self, address):
        """
        Register and return mock GET response for opensea landing page.
        """
        filepath = Path(self.samples_dir, "profile_not_found.html")
        with open(filepath, "r", encoding="utf-8") as fobj:
            html_content = fobj.read()

            return self.mock_responses.add(
                responses.GET,
                f"https://opensea.io/{address}",
                body=html_content
            )

    def test_parent(self):
        """ Assert that the scraper is a child of BaseScraper. """
        self.assertTrue(isinstance(self.client, BaseScraper))

    def test_request_logic(self):
        """
        Assert that the scraper takes the following steps:
            1. Makes a request to the opensea home page.
            2. Makes a request to the opensea address page.
        """
        # set up test
        # register expected requests in particular order
        # pylint: disable=protected-access
        self.mock_responses._set_registry(OrderedRegistry)
        first = self._mock_landing_page_resp()
        second = self._mock_profile_found_page_resp(self.test_addr)

        # run the job
        self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        self.assertEqual(first.call_count, 1)
        self.assertEqual(second.call_count, 1)

    def test_opensea_profile_found(self):
        """
        Assert that a nametag is added to the database
        when an Opensea profile is found.
        """
        # set up test
        # register expected requests
        self._mock_landing_page_resp()
        self._mock_profile_found_page_resp(self.test_addr)

        # assert there are no matching Tags in the database before scraping
        self.assertFalse(
            Tag.objects.filter(address=self.test_addr)
            .exists()
        )

        # run the job
        self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        tag = Tag.objects.filter(address=self.test_addr)[0]
        value = tag.nametag
        self.assertIn("thgirbx", value)
        self.assertIn("Joined October 2019", value)
        self.assertIn("Collected: 351", value)
        self.assertIn("Created: 3", value)
        self.assertIn("Favorited: 8", value)
        self.assertIn("https://twitter.com/seekmine", value)

    def test_opensea_profile_not_found(self):
        """
        Assert that a nametag is not added to the database
        when an Opensea profile cannot be found.
        """
        # set up test
        # register expected requests
        self._mock_landing_page_resp()
        self._mock_profile_not_found_page_resp(self.test_addr)

        # assert there are no matching Tags in the database before scraping
        self.assertFalse(
            Tag.objects.filter(address=self.test_addr)
            .exists()
        )

        # run the job
        self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # assert there are no matching Tags in the database after scraping
        self.assertFalse(
            Tag.objects.filter(address=self.test_addr)
            .exists()
        )
