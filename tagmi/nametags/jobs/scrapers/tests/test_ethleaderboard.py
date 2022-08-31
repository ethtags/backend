"""
Module containing tests for the ethleaderboard.py scraper.
"""
# std lib imports
from pathlib import Path
from unittest import mock
import json

# third party imports
from responses import matchers
from responses.registries import OrderedRegistry
import responses

# our imports
from ....basetest import BaseTestCase
from .. import ethleaderboard
from ..base_scraper import BaseScraper
from ....models import Tag


class EthleaderboardTests(BaseTestCase):
    """
    Tests the ethleaderboard scraper.
    """

    # pylint: disable=too-many-instance-attributes
    def setUp(self):
        """ Runs before each test. """

        super().setUp()
        self.client = ethleaderboard.EthleaderboardScraper()
        self.samples_dir = Path(__file__).parent.joinpath(
            "./samples/ethleaderboard"
        )

        # ens name used for tests
        self.test_ens_name = "master.eth"

        # data when no results are found
        self.no_results_resp = {"frens": [], "count": 0, "response_time": 638}

        # data when single result is found
        with open(
            self.samples_dir.joinpath("single_result.json"),
            "r",
            encoding="utf-8"
        ) as fobj:
            self.single_result_resp = json.loads(fobj.read())

        # data when multiple results are found
        with open(
            self.samples_dir.joinpath("multiple_results.json"),
            "r",
            encoding="utf-8"
        ) as fobj:
            self.multi_results_resp = json.loads(fobj.read())

    def _mock_landing_page_resp(self):
        """
        Register and return mock GET response for
        ethleaderboard landing page.
        """
        return self.mock_responses.add(
            responses.GET, "https://ethleaderboard.xyz/"
        )

    def _mock_results_resp(self, resp_json, ens_name):
        """
        Register and return mock GET response for querying
        an ENS name on ethleaderboard.
        """
        return self.mock_responses.add(
            responses.GET,
            "https://ethleaderboard.xyz/api/frens",
            match=[
                # expects certain headers to be there
                matchers.header_matcher(
                    ethleaderboard.get_frens_req_headers()
                ),
                # expects certain query string
                matchers.query_string_matcher(f"q={ens_name}")
            ],
            json=resp_json  # response json
        )

    def test_parent(self):
        """ Assert that the scraper is a child of BaseScraper. """
        self.assertTrue(isinstance(self.client, BaseScraper))

    def test_request_logic_ens_found(self):
        """
        Assert that the scraper takes the following steps
        when the address being searched resolves to an ENS name:
            1. Looks up an ENS name for the address.
            2. Makes a request to the ethleaderboard home page.
            3. Updates its headers, and makes a request to query the ens name.
        """
        # set up test
        # register expected requests in particular order
        # pylint: disable=protected-access
        self.mock_responses._set_registry(OrderedRegistry)
        first = self._mock_landing_page_resp()
        second = self._mock_results_resp(
            self.no_results_resp,
            self.test_ens_name
        )

        # make the address resolve to an ens name
        # then run the job
        with mock.patch("ens.ENS") as mock_ens:
            mock_ens.return_value.name.return_value = self.test_ens_name
            self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        self.assertEqual(mock_ens.return_value.name.call_count, 1)
        self.assertEqual(first.call_count, 1)
        self.assertEqual(second.call_count, 1)

    def test_request_logic_ens_not_found(self):
        """
        Assert that the scraper takes the following steps
        when the address being searched does NOT resolve to an ENS name:
            1. Looks up an ENS name for the address.
            2. Returns without making any requests to ethleaderboard.
            Note that we did not registering any mock responses, and
            so when the test passes, it is implicitly asserting that
            no requests were made.
        """
        # set up test without registering any mock responses

        # make the address NOT resolve to an ens name
        # then run the job
        with mock.patch("ens.ENS") as mock_ens:
            mock_ens.return_value.name.return_value = None
            job = self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        self.assertEqual(mock_ens.return_value.name.call_count, 1)
        self.assertEqual(job.result, None)

    def test_single_handle_found(self):
        """
        Assert that a single nametag is added to the database
        when ethleaderboard returns a single twitter handle.
        """
        # set up test
        # register expected requests
        self._mock_landing_page_resp()
        self._mock_results_resp(
            self.single_result_resp,
            self.test_ens_name
        )

        # make the address resolve to an ens name
        # then run the job
        with mock.patch("ens.ENS") as mock_ens:
            mock_ens.return_value.name.return_value = self.test_ens_name
            self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        tags = Tag.objects.filter(address=self.test_addr)
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].nametag, "https://twitter.com/seekmine")

    def test_multiple_handles_found(self):
        """
        Assert that a single nametag is added to the database
        when ethleaderboard returns multiple twitter handles.
        Assert that there are multiple twitter handles within
        that nametag.
        """
        # set up test
        # register expected requests
        self._mock_landing_page_resp()
        self._mock_results_resp(
            self.multi_results_resp,
            self.test_ens_name
        )

        # make the address resolve to an ens name
        # then run the job
        with mock.patch("ens.ENS") as mock_ens:
            mock_ens.return_value.name.return_value = self.test_ens_name
            self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        tags = Tag.objects.filter(address=self.test_addr)
        self.assertEqual(len(tags), 1)
        nametag = tags[0].nametag
        self.assertIn("https://twitter.com/seekmine", nametag)
        self.assertIn("https://twitter.com/master_setup", nametag)
        self.assertIn("https://twitter.com/YllwMasteR", nametag)
        self.assertIn("https://twitter.com/EkeneTheMaster", nametag)
        self.assertIn("https://twitter.com/MartinCincura", nametag)

    def test_no_labels_found(self):
        """
        Assert that 0 nametags are added to the database
        when ethleaderboard returns 0 results.
        Assert that the job returns None.
        """
        # set up test
        # register expected requests
        self._mock_landing_page_resp()
        self._mock_results_resp(
            self.no_results_resp,
            self.test_ens_name
        )

        # make the address resolve to an ens name
        # then run the job
        with mock.patch("ens.ENS") as mock_ens:
            mock_ens.return_value.name.return_value = self.test_ens_name
            job = self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        self.assertFalse(
            Tag.objects.filter(address=self.test_addr).exists(),
        )
        self.assertEqual(job.result, None)
