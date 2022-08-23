"""
Module containing tests for the dune.py scraper.
"""
# std lib imports
from pathlib import Path
from unittest import mock

# third party imports
from responses import matchers
from responses.registries import OrderedRegistry
import responses

# our imports
from ....basetest import BaseTestCase
from .. import dune
from ..base_scraper import BaseScraper
from ....models import Tag


@mock.patch("nametags.jobs.scrapers.dune.time", mock.MagicMock())
class DuneTests(BaseTestCase):
    """
    Tests the dune scraper.
    """

    # pylint: disable=too-many-instance-attributes
    def setUp(self):
        """ Runs before each test. """

        super().setUp()
        self.client = dune.DuneScraper()
        self.samples_dir = Path(__file__).parent.joinpath("./samples/dune")

        # fake response data for csrf request
        self.csrf_resp = {
            "csrf": "6a9zA7BoVqYCZ32mVfNa3kb2dq5DsnwHr8Vgv1BzK88"
        }

        # parts of fake response data for list labels request
        self.address_id = f"\\x{self.test_addr[2:]}"
        self.label = "stonercats"
        self.type1 = "contract_name"
        self.type2 = "project"

        # fake response for list labels request
        self.single_label_resp = [
            {
                "address_id": self.address_id,
                "id": 798651360,
                "type": self.type1,
                "name": self.label,
                "source": "ethereum_mainnet_contracts",
                "author": "dune",
                "updated_at": "2021-07-30T11:55:04.497829+00:00",
                "__typename": "ethereum_labels"
            }
        ]

        # fake response for list labels request
        self.multi_label_resp = [
            self.single_label_resp[0],
            {
                "address_id": self.address_id,
                "id": 798651343,
                "type": self.type2,
                "name": self.label,
                "source": "ethereum_mainnet_contracts",
                "author": "dune",
                "updated_at": "2021-07-30T11:55:04.497829+00:00",
                "__typename": "ethereum_labels"
            }
        ]

    def _mock_landing_page_resp(self):
        """
        Register and return mock GET response for dune labels landing page.
        """
        return self.mock_responses.add(
            responses.GET, "https://dune.com/labels"
        )

    def _mock_csrf_resp(self):
        """
        Register and return mock POST response for dune csrf endpoint.
        """
        return self.mock_responses.add(
            responses.POST,
            "https://dune.com/api/auth/csrf",
            match=[
                # expects certain headers to be there
                matchers.header_matcher(dune.csrf_req_headers)
            ],
            json=self.csrf_resp  # response json
        )

    def _mock_list_labels_resp(self, resp_json):
        """
        Register and return mock POST response for listing labels endpoint.
        """
        return self.mock_responses.add(
            responses.POST,
            "https://dune.com/api/labels/list",
            match=[
                # expects certain headers to be there
                matchers.header_matcher(
                    dune.get_labels_req_headers(self.test_addr)
                ),
                # expects certain request body in json
                matchers.json_params_matcher(
                    {
                        "csrf": self.csrf_resp["csrf"],
                        "address_id": self.address_id
                    }
                )
            ],
            json=resp_json  # response json
        )

    def test_parent(self):
        """ Assert that the scraper is a child of BaseScraper. """
        self.assertTrue(isinstance(self.client, BaseScraper))

    def test_request_logic(self):
        """
        Assert that the scraper takes the following steps:
            1. Makes a request to the dune labels home page.
            2. Updates its headers, and makes a request to get a csrf token.
            3. Updates its headers and makes a request to list the
               labels of an address.
        """
        # set up test
        # register expected requests in particular order
        # pylint: disable=protected-access
        self.mock_responses._set_registry(OrderedRegistry)
        first = self._mock_landing_page_resp()
        second = self._mock_csrf_resp()
        third = self._mock_list_labels_resp(self.single_label_resp)

        # run the job
        self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        self.assertEqual(first.call_count, 1)
        self.assertEqual(second.call_count, 1)
        self.assertEqual(third.call_count, 1)

    def test_single_label_found(self):
        """
        Assert that a single nametag is added to the database
        when Dune returns a single label.
        """
        # set up test
        # register expected requests
        self._mock_landing_page_resp()
        self._mock_csrf_resp()
        self._mock_list_labels_resp(self.single_label_resp)

        # assert there are no matching Tags in the database before scraping
        nametag = f"{self.type1}: {self.label}"
        self.assertFalse(
            Tag.objects.filter(address=self.test_addr, nametag=nametag)
            .exists()
        )

        # run the job
        self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        self.assertTrue(
            Tag.objects.filter(address=self.test_addr, nametag=nametag)
            .exists()
        )

    def test_multiple_labels_found(self):
        """
        Assert that multiple nametags are added to the database
        when Dune returns multiple labels.
        """
        # set up test
        # register expected requests
        self._mock_landing_page_resp()
        self._mock_csrf_resp()
        self._mock_list_labels_resp(self.multi_label_resp)

        # assert there are no matching Tags in the database before scraping
        nametag_one = f"{self.type1}: {self.label}"
        self.assertFalse(
            Tag.objects.filter(address=self.test_addr, nametag=nametag_one)
            .exists()
        )
        nametag_two = f"{self.type2}: {self.label}"
        self.assertFalse(
            Tag.objects.filter(address=self.test_addr, nametag=nametag_two)
            .exists()
        )

        # run the job
        self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        self.assertTrue(
            Tag.objects.filter(address=self.test_addr, nametag=nametag_one)
            .exists()
        )
        self.assertTrue(
            Tag.objects.filter(address=self.test_addr, nametag=nametag_two)
            .exists()
        )

    def test_no_labels_found(self):
        """
        Assert that 0 nametags are added to the database
        when Dune returns 0 labels.
        Assert that the job returns None.
        """
        # set up test
        # register expected requests
        self._mock_landing_page_resp()
        self._mock_csrf_resp()
        self._mock_list_labels_resp([])  # 0 labels to be returned

        # assert that there are no Tags in the database before scraping
        self.assertFalse(
            Tag.objects.filter(address=self.test_addr).exists()
        )

        # run the job
        self.queue.enqueue(self.client.run, job_id=self.test_addr)

        # make assertions
        # assert that there are no Tags in the database after scraping
        self.assertFalse(
            Tag.objects.filter(address=self.test_addr).exists()
        )
