"""
Module containing scraper jobs.
"""
# std lib imports

# third party imports

# our imports
from .scrapers.dune import DuneScraper
from .scrapers.etherscan import EtherscanScraper


class ScraperJob():
    """
    Base scraper job.
    """

    @property
    def name(self):
        """ Returns name of scraper job. Should be implemented by child. """
        raise NotImplementedError("Must subclass and override this method.")

    def run(self):
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

    def run(self):
        """
        Runs the etherscan scraper.
        """
        scraper = EtherscanScraper()
        return scraper.run()


class DuneScraperJob(ScraperJob):
    """
    Job that looks up an address on dune labels.
    """

    @property
    def name(self):
        """ Returns the name of the scraper job. """

        return "dune_scraper"

    def run(self):
        """
        Runs the dune scraper.
        """
        scraper = DuneScraper()
        return scraper.run()
