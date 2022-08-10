"""
Module containing base test class for the scraper tests.
"""
# std lib imports
from pathlib import Path

# third party imports

# our imports
from ...basetest import BaseTestCase


class BaseScraperTestCase(BaseTestCase):
    """
    Base class for the job tests.
    """

    def setUp(self):
        """ Runs before each test. """
        super().setUp()

        # directory containing html samples
        self.samples_dir = Path(__file__).parent.joinpath("./samples")
