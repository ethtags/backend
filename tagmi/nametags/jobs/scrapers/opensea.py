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
        twitter = self._parse_twitter(tree)
        collected = self._parse_collected(tree)
        created = self._parse_created(tree)
        favorited = self._parse_favorited(tree)
        label = f"Username: {username} - Twitter: {twitter} - " \
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

    def _parse_twitter(self, lxml_tree):
        """
        Returns twitter profile link as a string.
        Returns None if twitter link does not exist.
        """
        twitter = lxml_tree.xpath("/html/body/div[1]/div/main/div/div/div/div[3]/div/div/div[2]/div/div/div[1]/div/div[1]/a")  # noqa: E501 pylint: disable=line-too-long

        if len(twitter) != 0:
            twitter = twitter[0].get("href")
        else:
            twitter = None

        return twitter

    def _parse_collected(self, lxml_tree):
        """
        Returns number of collected NFTs as a string.
        Returns 0 if no info can be found.
        """
        collected = lxml_tree.xpath("/html/body/div[1]/div/main/div/div/div/div[5]/div/div[2]/div/div/nav/div[1]/ul/div/li[2]/a/span[2]")  # noqa: E501 pylint: disable=line-too-long

        if len(collected) != 0:
            collected = collected[0].text
        else:
            collected = "0"

        return collected

    def _parse_created(self, lxml_tree):
        """
        Returns number of created NFTs as a string.
        Returns 0 if no info can be found.
        """
        created = lxml_tree.xpath("/html/body/div[1]/div/main/div/div/div/div[5]/div/div[2]/div/div/nav/div[1]/ul/div/li[3]/a/span[2]")  # noqa: E501 pylint: disable=line-too-long

        if len(created) != 0:
            created = created[0].text
        else:
            created = "0"

        return created

    def _parse_favorited(self, lxml_tree):
        """
        Returns number of favorited NFTs as a string.
        Returns 0 if no info can be found.
        """
        favorited = lxml_tree.xpath("/html/body/div[1]/div/main/div/div/div/div[5]/div/div[2]/div/div/nav/div[1]/ul/div/li[4]/a/span[2]")  # noqa: E501 pylint: disable=line-too-long

        if len(favorited) != 0:
            favorited = favorited[0].text
        else:
            favorited = "0"

        return favorited
