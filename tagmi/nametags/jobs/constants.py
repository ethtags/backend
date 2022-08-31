""" Module containing a list of scrapers to run. """
# std lib imports

# third party imports

# our imports
from . import scraper_jobs


scraper_jobs_to_run = [
    scraper_jobs.DuneScraperJob,
    scraper_jobs.EtherscanScraperJob,
    scraper_jobs.OpenseaScraperJob,
    scraper_jobs.EthleaderboardScraperJob
]


def noop():
    """
    Empty function that runs after job dependencies have finished running.
    """
    return None
