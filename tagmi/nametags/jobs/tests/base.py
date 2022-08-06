"""
Module containing tests for the etherscan.py scraper.
"""
# std lib imports
from unittest import TestCase

# third party imports
import fakeredis
import rq

# our imports


class BaseTestCase(TestCase):
    """
    Base class for the job tests.
    """

    def setUp(self):
        """ Runs before each test. """
        super().setUp()

        # address to be used in tests
        self.test_addr = "0x7F101fE45e6649A6fB8F3F8B43ed03D353f2B90c".lower()

        # fake redis backend and queue
        self.fake_redis = fakeredis.FakeRedis(fakeredis.FakeServer())
        self.queue = rq.Queue(connection=self.fake_redis, is_async=False)

    def tearDown(self):
        """ Runs after each test. """
        super().tearDown()
        self.fake_redis.flushall()
