"""
Module containing etherscan scraper.
"""
# std lib imports

# third party imports
import rq

# our imports
from . import base
from ..models import Tag


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
        """
        # make request to etherscan home page
        self.get("https://etherscan.io/")

        # update headers
        self.headers.update(subsequent_headers)

        # make request to lookup address
        address = rq.get_current_job().get_id()
        resp = self.get(f"https://etherscan.io/address/{address}/")

        # parse data
        label = parse_address_label(resp.text)
        print("label: ", label)

        # store data in database
        if label is not None:
            print("got here")
            Tag.objects.create(
                address=address,
                nametag=label,
                source="etherscan"
            )


def parse_address_label(html_content):
    """
    Returns the address label if it exists in the html_content.
    Returns None otherwise.
    """
