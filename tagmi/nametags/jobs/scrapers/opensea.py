"""
Module containing etherscan scraper.
"""
# std lib imports
import logging
import time

# third party imports
import lxml.html
import rq

# our imports
from .base_scraper import BaseScraper
from .utils import add_label_to_db


logger = logging.getLogger(__name__)


class OpenseaScraper(BaseScraper):
    """
    Opensea scraper.
    """

    def run(self):
        """
        Looks up an address on Opensea.
        If the address has an associated profile, a label is
        added to the nametags table of the database.
        Returns a label if a profile is found.
        Returns None if no profile is found.
        """
        # make request to opensea home page
        logger.info("making GET to opensea home page")
        self.get("https://opensea.io/")
        time.sleep(2)

        # make profile request
        address = rq.get_current_job().get_id()[0:42]
        logger.info("making GET to opensea profile page")
        resp = self.get(f"https://opensea.io/{address}")

        # parse label
        label = self.parse_label(resp.text)

        # store label in database
        add_label_to_db(label, "opensea", address)

        return label

    def parse_label(self, html_content):
        """
        Returns a string of profile metadata if a profile exists.
        Returns None if a profile does not exist.
        """
        tree = lxml.html.fromstring(html_content)

        # check if profile exists
        joined = self._parse_joined(tree)

        # profile does not exist
        if joined is None:
            return None

        # build a string containing profile metadata
        username = self._parse_username(tree)
        socials = self._parse_socials(tree)
        collected = self._parse_tab(tree, "Collected")
        created = self._parse_tab(tree, "Created")
        favorited = self._parse_tab(tree, "Favorited")
        label = f"Username: {username} - Socials: {socials} - " \
                f"{joined} - Collected: {collected} - " \
                f"Created: {created} - Favorited: {favorited}"

        return label

    def _parse_joined(self, lxml_tree):
        """
        Returns profile joined date as a string.
        Returns None if joined data does not exist.
        """
        return lxml_tree.xpath("/html/body/div[1]/div/main/div/div/div/div[4]/div/div/div[1]/div/div/div[2]/div")[0].text  # noqa: E501 pylint: disable=line-too-long

    def _parse_username(self, lxml_tree):
        """
        Returns username as a string.
        Returns None if username does not exist.
        """
        return lxml_tree.xpath("/html/body/div[1]/div/main/div/div/div/div[3]/div/div/div[1]/div/div[2]/h1")[0].text  # noqa: E501 pylint: disable=line-too-long

    def _parse_socials(self, lxml_tree):
        """
        Returns social links as a string.
        Returns None if socials do not exist.
        """
        # find the social links
        share_div = lxml_tree.xpath('//*[@id="main"]/div/div/div/div[3]/div/div/div[2]/div/div/div[2]')  # noqa: E501 pylint: disable=line-too-long
        socials_div = share_div[0].getprevious()
        links = socials_div.iter(tag="a")

        # build the string
        to_ret = ""
        for link in links:
            href = link.get("href")
            to_ret += f"{href} "

        # return None if no socials were found
        if to_ret == "":
            return None

        # format the string
        to_ret = to_ret.strip()

        return to_ret

    def _parse_tab(self, lxml_tree, tab_text):
        """
        Returns the number that is next to the tab with
        the given text. E.g, "Collected", "Created", etc.
        Returns 0 if tab or number could not be found.
        """
        # find tab with the given text
        tab = lxml_tree.xpath(f'//span[contains(text(),"{tab_text}")]')
        if len(tab) == 0:
            return "0"

        # sibling element that contains number
        amount = tab[0].getnext()
        if amount is None:
            return "0"

        return amount.text
