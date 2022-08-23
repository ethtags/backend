"""
Module containing tests for the etherscan.py scraper.
"""
# std lib imports
from unittest import mock
from pathlib import Path

# third party imports
from responses import matchers
from responses.registries import OrderedRegistry
import responses

# our imports
from ....basetest import BaseTestCase
from .. import etherscan
from ..base_scraper import BaseScraper
from ....models import Tag


class EtherscanTests(BaseTestCase):
    """
    Tests the etherscan scraper.
    """

    def setUp(self):
        """ Runs before each test. """

        super().setUp()
        self.client = etherscan.EtherscanScraper()
        self.samples_dir = Path(__file__).parent.joinpath(
            "./samples/etherscan"
        )

    def test_job_parent(self):
        """ Assert that the scraper is a child of the Base parent. """
        self.assertTrue(isinstance(self.client, BaseScraper))

    def test_request_logic(self):
        """
        Assert that the job takes the following steps:
            1. Makes a request to the etherscan home page.
            2. Updates its headers.
            3. Makes a request to lookup the desired address.
        """
        # set up test
        # register expected requests in particular order
        # pylint: disable=protected-access
        self.mock_responses._set_registry(OrderedRegistry)
        first = self.mock_responses.add(responses.GET, "https://etherscan.io/")
        second = self.mock_responses.add(
            responses.GET,
            f"https://etherscan.io/address/{self.test_addr}/",
            match=[
                # expects certain headers to be there
                matchers.header_matcher(etherscan.subsequent_headers)
            ]
        )

        # run the job
        self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        self.assertEqual(first.call_count, 1)
        self.assertEqual(second.call_count, 1)

    @mock.patch(
        "nametags.jobs.scrapers.etherscan.EtherscanScraper.parse_address_label"
    )
    def test_address_lookup_found(self, mock_parse_label):
        """
        Assert that a nametag is added to the database if it
        is found during an address lookup.
        """
        # set up test
        fake_tag = "Etherscan Address Label"
        mock_parse_label.return_value = fake_tag

        # register expected requests in particular order
        # pylint: disable=protected-access
        self.mock_responses._set_registry(OrderedRegistry)
        self.mock_responses.add(responses.GET, "https://etherscan.io/")
        self.mock_responses.add(
            responses.GET,
            f"https://etherscan.io/address/{self.test_addr}/",
            match=[
                # expects certain headers to be there
                matchers.header_matcher(etherscan.subsequent_headers)
            ]
        )

        # run the job
        self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        tag = Tag.objects.get(nametag=fake_tag)
        self.assertEqual(tag.nametag, fake_tag)

    @mock.patch(
        "nametags.jobs.scrapers.etherscan.EtherscanScraper.parse_address_label"
    )
    @mock.patch(
        "nametags.jobs.scrapers.etherscan.EtherscanScraper.parse_token_label"
    )
    def test_address_lookup_not_found(self, mock_token, mock_address):
        """
        Assert that a token lookup is done if no label is found
        during an address lookup.
        """
        # set up test
        mock_address.return_value = None
        mock_token.return_value = None

        # register expected requests in particular order
        # pylint: disable=protected-access
        self.mock_responses._set_registry(OrderedRegistry)
        self.mock_responses.add(responses.GET, "https://etherscan.io/")
        self.mock_responses.add(
            responses.GET,
            f"https://etherscan.io/address/{self.test_addr}/",
            match=[
                # expects certain headers to be there
                matchers.header_matcher(etherscan.subsequent_headers)
            ]
        )
        token_lookup = self.mock_responses.add(
            responses.GET,
            f"https://etherscan.io/token/{self.test_addr}/",
            match=[
                # expects certain headers to be there
                matchers.header_matcher(etherscan.subsequent_headers)
            ]
        )

        # run the job
        self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        self.assertEqual(token_lookup.call_count, 1)
        self.assertEqual(mock_token.call_count, 1)

    @mock.patch(
        "nametags.jobs.scrapers.etherscan.EtherscanScraper.parse_address_label"
    )
    @mock.patch(
        "nametags.jobs.scrapers.etherscan.EtherscanScraper.parse_token_label"
    )
    def test_token_lookup_found(self, mock_parse_token, mock_parse_addr):
        """
        Assert that a nametag is added to the database if it
        is found during a token lookup.
        """
        # set up test
        mock_parse_addr.return_value = None
        fake_tag = "Etherscan Token Label"
        mock_parse_token.return_value = fake_tag

        # register expected requests in particular order
        # pylint: disable=protected-access
        self.mock_responses._set_registry(OrderedRegistry)
        self.mock_responses.add(responses.GET, "https://etherscan.io/")
        self.mock_responses.add(
            responses.GET,
            f"https://etherscan.io/address/{self.test_addr}/",
            match=[
                # expects certain headers to be there
                matchers.header_matcher(etherscan.subsequent_headers)
            ]
        )
        self.mock_responses.add(
            responses.GET,
            f"https://etherscan.io/token/{self.test_addr}/",
            match=[
                # expects certain headers to be there
                matchers.header_matcher(etherscan.subsequent_headers)
            ]
        )

        # run the job
        self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        tag = Tag.objects.get(nametag=fake_tag)
        self.assertEqual(tag.nametag, fake_tag)

    @mock.patch(
        "nametags.jobs.scrapers.etherscan.EtherscanScraper.parse_address_label"
    )
    @mock.patch(
        "nametags.jobs.scrapers.etherscan.EtherscanScraper.parse_token_label"
    )
    def test_token_lookup_not_found(self, mock_parse_addr, mock_parse_token):
        """
        Assert that no nametag is added to the database if it
        can't be found in an address or token lookup.
        """
        # set up test
        mock_parse_addr.return_value = None
        mock_parse_token.return_value = None
        expected_count = Tag.objects.count()

        # register expected requests in particular order
        # pylint: disable=protected-access
        self.mock_responses._set_registry(OrderedRegistry)
        self.mock_responses.add(responses.GET, "https://etherscan.io/")
        self.mock_responses.add(
            responses.GET,
            f"https://etherscan.io/address/{self.test_addr}/",
            match=[
                # expects certain headers to be there
                matchers.header_matcher(etherscan.subsequent_headers)
            ]
        )
        self.mock_responses.add(
            responses.GET,
            f"https://etherscan.io/token/{self.test_addr}/",
            match=[
                # expects certain headers to be there
                matchers.header_matcher(etherscan.subsequent_headers)
            ]
        )

        # run the job
        self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        self.assertEqual(Tag.objects.count(), expected_count)

    def test_parse_address_label(self):
        """
        Assert that a label is returned if it is found
        in the html content of an address lookup.
        """
        # set up test
        address_lookup_html = Path(self.samples_dir, "address_lookup.html")
        with open(address_lookup_html, "r", encoding="utf-8") as fobj:
            html_content = fobj.read()

        # make request
        label = self.client.parse_address_label(html_content)

        # make assertions
        self.assertEqual(label, "Flexpool.io")

    def test_parse_address_label_not_found(self):
        """
        Assert that None is returned if a label is not found
        in the html content of an address lookup.
        """
        # set up text
        html_content = "<html><body>Flex No Pool</body></html>"

        # make request
        label = self.client.parse_address_label(html_content)

        # make assertions
        self.assertEqual(label, None)

    def test_parse_token_label(self):
        """
        Assert that a label is returned if it is found
        in the html content of a token lookup.
        """
        # set up test
        token_lookup_html = Path(self.samples_dir, "token_lookup.html")
        with open(token_lookup_html, "r", encoding="utf-8") as fobj:
            html_content = fobj.read()

        # make request
        label = self.client.parse_token_label(html_content)

        # make assertions
        self.assertEqual(label, "Tether USD")

    def test_parse_token_label_not_found(self):
        """
        Assert that None is returned if a label is not found
        in the html content of a token lookup.
        """
        # set up text
        html_content = "<html><body>Nothing here</body></html>"

        # make request
        label = self.client.parse_token_label(html_content)

        # make assertions
        self.assertEqual(label, None)
