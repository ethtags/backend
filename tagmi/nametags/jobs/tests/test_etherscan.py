"""
Module containing tests for the etherscan.py scraper.
"""
# std lib imports
from unittest import mock

# third party imports
from responses import matchers
from responses.registries import OrderedRegistry
import fakeredis
import responses
import rq

# our imports
from .base import BaseTestCase
from ..base import BaseScraper
from .. import etherscan
from ...models import Tag


class EtherscanTests(BaseTestCase):
    """
    Tests the etherscan scraper.
    """

    # TODO
    # mock an etherscan response for an address and test that the correct results is parsed
    # test that a request is made to the token lookup page if no label is found on the address lookup page

    def setUp(self):
        """ Runs before each test. """

        super().setUp()
        self.client = etherscan.Etherscan()

    def tearDown(self):
        """ Runs after each test. """

        self.fake_redis.flushall()
        super().tearDown()

    def test_job_parent(self):
        """ Assert that the scraper is a child of the Base parent. """
        self.assertTrue(isinstance(self.client, BaseScraper))

    @responses.activate(registry=OrderedRegistry)
    def test_request_logic(self):
        """
        Assert that the job takes the following steps:
            1. Makes a request to the etherscan home page.
            2. Updates its headers.
            3. Makes a request to lookup the desired address.
        """
        # set up test
        # register expected requests in particular order
        first = responses.add(responses.GET, "https://etherscan.io/")
        second = responses.add(
            responses.GET,
            f"https://etherscan.io/address/{self.test_addr.lower()}/",
            match=[
                # expects certain headers to be there
                matchers.header_matcher(etherscan.subsequent_headers)
            ]
        )

        # run the job
        self.queue.enqueue(self.client.run, job_id=self.test_addr.lower())

        # make assertions
        self.assertEqual(first.call_count, 1)
        self.assertEqual(second.call_count, 1)

    def test_response_logic(self):
        """
        Assert that the job takes the following steps:
            4. Tries to parse label.
                4a. If label is not found, makes a token lookup request.
                4b. Tries to parse label.
            5. If label is found, adds it to Nametags database.
        """
        assert False
 
    @mock.patch("nametags.jobs.etherscan.parse_address_label")
    def test_address_lookup_tag_found(self, mock_parse_label):
        """
        Assert that a nametag is added to the database if it
        is found during an address lookup.
        """
        # set up test
        fake_tag = "Etherscan Address Label"
        mock_parse_label.return_value = fake_tag

        # register expected requests in particular order
        responses.add(responses.GET, "https://etherscan.io/")
        responses.add(
            responses.GET,
            f"https://etherscan.io/address/{self.test_addr}/",
            match=[
                # expects certain headers to be there
                matchers.header_matcher(etherscan.subsequent_headers)
            ]
        )

        # run the job
        job = self.queue.enqueue(self.client.run, job_id=self.test_addr.lower())
        job.refresh()
        print("job.result: ", job.result)
        print("job.exc_info: ", job.exc_info)

        # make assertions
        tag = Tag.objects.get(nametag=fake_tag)
        self.assertEqual(tag.nametag, fake_tag)
