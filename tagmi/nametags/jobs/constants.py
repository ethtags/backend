""" Module containing a list of scrapers to run. """
# std lib imports

# third party imports

# our imports
from .scraper_jobs import DuneScraperJob, EtherscanScraperJob, \
    OpenseaScraperJob


scraper_jobs_to_run = [
    DuneScraperJob,
    EtherscanScraperJob,
    OpenseaScraperJob
]


def noop():
    """
    Empty function that runs after job dependencies have finished running.
    """
    return None
