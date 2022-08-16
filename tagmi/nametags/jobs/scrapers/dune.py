"""
Module containing etherscan scraper.
"""
# std lib imports
import uuid

# third party imports
import rq

# our imports
from .base_scraper import BaseScraper
from ...models import Address, Tag


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
        to_ret = []

        # make request to dune labels home page
        self.get("https://dune.com/labels")

        # update headers and make csrf request
        self.headers.update(csrf_req_headers)
        self.headers.pop("Sec-Fetch-User")
        resp = self.post("https://dune.com/api/auth/csrf")
        data = resp.json()
        csrf = data["csrf"]

        # update headers and make labels list request
        address = rq.get_current_job().get_id()
        self.headers.update(
            get_labels_req_headers(address)
        )
        resp = self.post(
            "https://dune.com/api/labels/list",
            json={"csrf": csrf, "address_id": f"\\x{address[2:]}"}
        )
        data = resp.json()

        # store labels in database
        for item in data:
            # get or create address
            address_obj, _ = Address.objects.get_or_create(
                pubkey=address
            )

            # get or create nametag
            nametag = f"{item['type']}: {item['name']}"
            Tag.objects.get_or_create(
                address=address_obj,
                nametag=nametag,
                created_by_session_id=str(uuid.uuid4()),
                source="dune"
            )
            to_ret.append(nametag)

        # return list of labels or None
        if len(to_ret) != 0:
            return to_ret

        return None
