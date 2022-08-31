"""
Module containing etherscan scraper.
"""
# std lib imports
import logging
import time

# third party imports
import rq

# our imports
from .base_scraper import BaseScraper
from .utils import add_label_to_db


logger = logging.getLogger(__name__)
csrf_req_headers = {
    "Accept": "*/*",
    "Referer": "https://dune.com/labels",
    "Content-Type": "application/json",
    "Origin": "https://dune.com",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "TE": "trailers"
}


def get_labels_req_headers(address):
    """
    Returns dictionary of headers that should be
    sent in the request to list labels of an address.
    """
    return {
        "Referer": f"https://dune.com/labels/ethereum/{address}"
    }


class DuneScraper(BaseScraper):
    """
    Dune scraper.
    """

    def run(self):
        """
        Looks up an address on Dune labels.
        If the address has an associated label, the label is
        added to the nametags table of the database.
        Returns a list of labels if they are found.
        Returns None if no label is found.
        """
        # make request to dune labels home page
        logger.info("making GET to dune labels home page")
        self.get("https://dune.com/labels")
        time.sleep(2)

        # update headers and make csrf request
        logger.info("making POST to dune csrf endpoint")
        self.headers.update(csrf_req_headers)
        self.headers.pop("Sec-Fetch-User")
        resp = self.post("https://dune.com/api/auth/csrf")
        data = resp.json()
        csrf = data["csrf"]
        time.sleep(1)

        # update headers and make labels list request
        address = rq.get_current_job().get_id()[0:42]
        self.headers.update(
            get_labels_req_headers(address)
        )
        logger.info("making POST to dune list labels")
        body = {"csrf": csrf, "address_id": f"\\x{address[2:]}"}
        resp = self.post(
            "https://dune.com/api/labels/list",
            json=body
        )
        data = resp.json()

        # build nametag from labels
        nametag = ""
        count = 0
        for item in data:
            # only get first 10 labels
            if count == 10:
                nametag += ", and more..."
                break

            # pull label from json
            label = f"{item['name']}"
            nametag += f", {label}"

            # increment counter
            count += 1

        # return if nametag is empty
        if nametag == "":
            return None

        # strip ", " from beginning of nametag
        nametag = nametag[2:]

        # store nametag in database and return it
        add_label_to_db(nametag, "dune", address)

        return nametag
