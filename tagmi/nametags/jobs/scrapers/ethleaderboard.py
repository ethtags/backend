"""
Module containing ethleaderboard scraper.
"""
# std lib imports
import logging
import re
import time

# third party imports
import ens
import rq

# our imports
from .base_scraper import BaseScraper
from .utils import add_label_to_db, web3_provider


logger = logging.getLogger(__name__)


def get_frens_req_headers():
    """
    Returns dictionary of headers that should be
    sent in the request to list labels of an address.
    """
    return {
        "Referer": "https://ethleaderboard.xyz/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "TE": "trailers"
    }


class EthleaderboardScraper(BaseScraper):
    """
    Ethleaderboard scraper.
    """

    def run(self):
        """
        Looks up an ENS on Eth Leaderboard.
        If the ENS has an associated label, the label is
        added to the nametags table of the database.
        Returns a string of comma-separated labels if they are found.
        Returns None if the address does not resolve to an ENS name,
        or if no labels are found for the ENS name.
        """
        # check if the address resolves to an ENS name
        address = rq.get_current_job().get_id()[0:42]
        ens_obj = ens.ENS(web3_provider)
        logger.info("resolving %s to an ENS name", address)
        ens_name = ens_obj.name(address=address)

        if ens_name is None:
            logger.info("address did not resolve to an ENS name, exiting")
            return None

        # make request to ethleaderboard home page
        logger.info("making GET to ethleadboard home page")
        self.get("https://ethleaderboard.xyz/")
        time.sleep(2)

        # update headers and make request to get associated twitters
        logger.info("making GET to ethleaderboard frens/ endpoint")
        self.headers.update(get_frens_req_headers())
        resp = self.get(
            "https://ethleaderboard.xyz/api/frens",
            params={"q": ens_name}
        )
        data = resp.json()

        # build nametag from matching results
        nametag = ""
        pattern = re.compile(rf"(.*\s)*{re.escape(ens_name)}", re.IGNORECASE)
        for item in data["frens"]:
            # skip if no match found
            if not pattern.match(item['name']):
                continue

            # pull handle from json
            assert item['handle'] != ""
            label = f"https://twitter.com/{item['handle']}"
            nametag += f", {label}"

        # return if nametag is empty
        if nametag == "":
            return None

        # strip ", " from beginning of nametag
        nametag = nametag[2:]

        # store nametag in database and return it
        add_label_to_db(nametag, "ethleaderboard", address)

        return nametag
