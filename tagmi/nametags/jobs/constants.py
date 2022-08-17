""" Module containing a list of scrapers to run. """
# std lib imports

# third party imports

# our imports
from .scraper_jobs import DuneScraperJob, EtherscanScraperJob


scraper_jobs_to_run = [
    DuneScraperJob,
    EtherscanScraperJob
]


def noop():
    """
    Empty function that runs after job dependencies have finished running.
    """
    return None
