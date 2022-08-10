"""
Module containing scraper jobs.
"""
# std lib imports

# third party imports

# our imports
from .scrapers.etherscan import EtherscanScraper


class ScraperJob():
    """
    Base scraper job.
    """

    @property
    def name(self):
        """ Returns name of scraper job. Should be implemented by child. """
        raise NotImplementedError("Must subclass and override this method.")

    @staticmethod
    def run():
        """ Does work. Should be implemented by child. """
        raise NotImplementedError("Must subclass and override this method.")


class EtherscanScraperJob(ScraperJob):
    """
    Job that looks up an address on etherscan.
    """

    @property
    def name(self):
        """ Returns the name of the scraper job. """

        return "etherscan_scraper"

    @staticmethod
    def run():
        """
        Runs the etherscan scraper.
        """
        scraper = EtherscanScraper()
        scraper.run()
