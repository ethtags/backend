"""
Module containing base test class for jobs and scrapers.
"""
# std lib imports
from unittest import TestCase

# third party imports
import fakeredis
import responses
import rq

# our imports


class BaseTestCase(TestCase):
    """
    Base class for the job tests.
    """

    def setUp(self):
        """ Runs before each test. """
        super().setUp()

        # fake redis backend and queue
        self.fake_redis = fakeredis.FakeRedis(fakeredis.FakeServer())
        self.queue = rq.Queue(connection=self.fake_redis, is_async=False)

        # fake requests/responses
        self.mock_responses = responses.RequestsMock()
        self.mock_responses.start()

        # address to be used in tests
        self.test_addr = "0x7F101fE45e6649A6fB8F3F8B43ed03D353f2B90c".lower()

    def tearDown(self):
        """ Runs after each test. """

        super().tearDown()

        # clean up fake redis
        self.fake_redis.flushall()

        # clean up fake requests/responses
        self.mock_responses.stop()
        self.mock_responses.reset()
