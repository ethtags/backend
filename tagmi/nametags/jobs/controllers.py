"""
Module containing job controllers.
"""
# std lib imports

# third party imports
from django.conf import settings
from rq.job import JobStatus
import redis
import rq

# our imports
from . import constants
from . import queue


class ScraperJobsController():
    """
    Class that handles scraper jobs.
    """

    def __init__(self, redis_cursor=None, redis_queue=None):
        """ Class initialization. """

        # create redis cursor if none given
        self.redis_cursor = redis_cursor
        if self.redis_cursor is None:
            self.redis_cursor = redis.from_url(settings.REDIS_URL)

        # create redis queue if none given
        self.redis_queue = redis_queue
        if self.redis_queue is None:
            self.redis_queue = queue.Queue(connection=self.redis_cursor)

    def create_jobs(self, address):
        """
        Creates a series of scraper jobs and adds them to the redis queue.
        Creates a final job that is run after all the previous
        jobs are completed. This acts as a record that all of the
        scraper jobs have finished running.
        """
        # enqueue scraper jobs
        jobs = []
        for source in constants.scraper_jobs_to_run:
            obj = source()
            jobs.append(
                self.redis_queue.enqueue(
                    obj.run,
                    job_id=f"{address}_{obj.name}"
                )
            )

        # create job that depends on the previous ones finishing
        dependents = rq.job.Dependency(
            jobs=jobs,
            allow_failure=True
        )
        self.redis_queue.enqueue(
            constants.noop,
            job_id=address,
            depends_on=dependents
        )

    def enqueue_if_stale(self, address):
        """
        Creates new scraping jobs if the current results are stale.

        Returns a tuple of (stale, enqueued) where:
            - stale (bool): jobs have not run recently for given address.
            - enqueued (bool): new jobs were enqueued in this function.
        """
        stale = enqueued = None

        try:
            # get job for given address
            job = rq.job.Job.fetch(address, self.redis_cursor)
            status = job.get_status(refresh=True)

            # job status is failed, stopped, cancelled
            # requeue the job, set stale to True
            if status in [
                JobStatus.FAILED,
                JobStatus.STOPPED,
                JobStatus.CANCELED
            ]:
                self.create_jobs(address)
                stale = True
                enqueued = True

            # job status is queued, started, deferred
            # do not requeue the job, set stale to True
            elif status in [
                JobStatus.QUEUED,
                JobStatus.STARTED,
                JobStatus.DEFERRED
            ]:
                stale = True
                enqueued = False

            # job status is finished (successful)
            # do not queue the job, set stale to False
            elif status in [JobStatus.FINISHED]:
                stale = False
                enqueued = False

            else:
                raise Exception(
                    f"Job {job} is in an undefined state, investigate."
                )

        # job cannot be found therefore it is stale
        # create new job, mark sources as stale
        except rq.exceptions.NoSuchJobError:
            self.create_jobs(address)
            stale = True
            enqueued = True

        assert stale is not None
        assert enqueued is not None
        return (stale, enqueued)
