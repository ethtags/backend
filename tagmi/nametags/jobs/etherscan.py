"""
Module containing etherscan scraper.
"""
# std lib imports
import uuid

# third party imports
import lxml.html
import rq

# our imports
from . import base
from ..models import Address, Tag


subsequent_headers = {
    "Referer": "https://etherscan.io/",
    "Sec-Fetch-Site": "same-origin",
    "TE": "trailers"
}


class Etherscan(base.BaseScraper):
    """
    Etherscan scraper.
    """

    def run(self):
        """
        Looks up an address on etherscan.
        If the address has an associated label, the label is
        added to the nametags table of the database.
        Returns the label if it is found.
        Returns None if no label is found.
        """
        # make request to etherscan home page
        self.get("https://etherscan.io/")

        # update headers
        self.headers.update(subsequent_headers)

        # lookup address and parse label
        address = rq.get_current_job().get_id()
        resp = self.get(f"https://etherscan.io/address/{address}/")
        label = Etherscan.parse_address_label(resp.text)

        # if address lookup found nothing, do token lookup
        if label is None:
            resp = self.get(f"https://etherscan.io/token/{address}/")
            label = Etherscan.parse_token_label(resp.text)

        # store label in database
        if label is not None:
            address_obj, _ = Address.objects.get_or_create(
                pubkey=address
            )
            Tag.objects.create(
                address=address_obj,
                nametag=label,
                created_by_session_id=str(uuid.uuid4()),
                source="etherscan"
            )

        return label

    @staticmethod
    def parse_address_label(html_content):
        """
        Returns the address label if it exists in the html_content.
        Returns None otherwise.
        """
        tree = lxml.html.fromstring(html_content)
        value = tree.xpath("/html/body/div[1]/main/div[4]/div[1]/div[1]/div/div[1]/div/span/span")  # noqa: E501 pylint: disable=line-too-long

        # match found
        if len(value) != 0:
            return value[0].text

        return None

    @staticmethod
    def parse_token_label(html_content):
        """
        Returns the token label if it exists in the html_content.
        Returns None otherwise.
        """
        tree = lxml.html.fromstring(html_content)
        value = tree.xpath(
            "/html/body/div[1]/main/div[1]/div/div[1]/h1/div/span"
        )

        # match found
        if len(value) != 0:
            return value[0].text

        return None
