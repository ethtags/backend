"""
Module containing base test class for jobs and scrapers.
"""
# std lib imports
from unittest import mock

# third party imports
from rest_framework.test import APITestCase
import fakeredis
import responses

# our imports
from .jobs import queue


class BaseTestCase(APITestCase):
    """
    Base class for the job tests.
    """

    def setUp(self):
        """ Runs before each test. """
        super().setUp()

        # fake redis backend and queue
        redis_patcher = mock.patch("redis.from_url", new=fakeredis.FakeRedis)
        redis_patcher.start()
        self.fake_redis = fakeredis.FakeRedis()
        self.queue = queue.Queue(connection=self.fake_redis, is_async=False)

        # fake requests/responses
        self.mock_responses = responses.RequestsMock()
        self.mock_responses.start()

        # address to be used in tests
        self.test_addr = "0x7F101fE45e6649A6fB8F3F8B43ed03D353f2B90c".lower()

        # clean up all mock patches
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        """ Runs after each test. """

        super().tearDown()

        # clean up fake redis
        self.fake_redis.flushall()

        # clean up fake requests/responses
        self.mock_responses.stop()
        self.mock_responses.reset()
