""" Module containins tests for the job controllers. """

# std lib imports
from unittest import mock

# third party imports
import rq

# our imports
from .basetest import BaseTestCase
from .controllers import ScraperJobsController


class PicklableMock(mock.Mock):
    """ Subclass of Mock that works with Pickle serialization. """

    def __reduce__(self):
        """ Support Pickle serialization. """
        return (mock.Mock, ())


class ScraperJobsControllerTests(BaseTestCase):
    """ Tests the ScraperJobsController class. """

    def setUp(self):
        """ Runs before each test. """

        super().setUp()
        self.controller = ScraperJobsController(
            redis_cursor=self.fake_redis,
            redis_queue=self.queue
        )

    @mock.patch("rq.job.Job.get_status")
    def test_sources_not_stale(self, mock_job_status):
        """
        Assert that retrieving an address when sources are not stale
        will NOT add a job to the redis queue.
        """
        # set up test
        # create an existing job for the address that is to be searched
        job = self.queue.enqueue(
            "",
            job_id=self.test_addr
        )
        expected_created_at = job.created_at

        # mock the job's status to be finished
        mock_job_status.return_value = rq.job.JobStatus.FINISHED

        # call controller
        stale, enqueued = self.controller.enqueue_if_stale(
            self.test_addr
        )

        # assert that sources are not stale and no new jobs were added
        self.assertFalse(stale)
        self.assertFalse(enqueued)
        job = rq.job.Job.fetch(
            self.test_addr,
            connection=self.fake_redis
        )
        self.assertEqual(job.created_at, expected_created_at)

    def test_stale_sources_job_dne(self):
        """
        Stale sources in this test means there is no key in redis
        with an ID matching the address that is being looked up.
        Assert that the controller adds a job to the redis queue.
        """
        # set up test
        # assert no jobs exist for the given address
        with self.assertRaises(rq.exceptions.NoSuchJobError):
            rq.job.Job.fetch(
                self.test_addr,
                connection=self.fake_redis
            )

        # call controller
        stale, enqueued = self.controller.enqueue_if_stale(self.test_addr)

        # make assertions
        # assert that a job was added to the queue
        # this would raise a NoSuchJobError otherwise
        rq.job.Job.fetch(
            self.test_addr,
            connection=self.fake_redis
        )
        self.assertTrue(enqueued)
        self.assertTrue(stale)

    @mock.patch("rq.job.Job.get_status")
    def test_stale_sources_job_in_progress(self, mock_job_status):
        """
        Stale sources in this test means a job exists for the
        address being searched, and the job is either
        queued, started, or deferred (waiting on dependencies).
        Assert that retrieving an address with jobs in progress
        will NOT add a job to the redis queue.
        """
        # set up test
        # create an existing job for the address that is to be searched
        job = self.queue.enqueue(
            "",
            job_id=self.test_addr
        )
        expected_created_at = job.created_at

        # mock the job's status to be queued, started, deferred
        to_test = [
            rq.job.JobStatus.QUEUED,
            rq.job.JobStatus.STARTED,
            rq.job.JobStatus.DEFERRED
        ]

        for status in to_test:
            # mock status
            mock_job_status.return_value = status

            # call controller and make assertions
            stale, enqueued = self.controller.enqueue_if_stale(
                self.test_addr
            )
            self.assertTrue(stale)
            self.assertFalse(enqueued)

            # assert that no new job was added to the queue
            job = rq.job.Job.fetch(
                self.test_addr,
                connection=self.fake_redis
            )
            self.assertEqual(job.created_at, expected_created_at)

    @mock.patch("rq.job.Job.get_status")
    def test_stale_sources_job_failed(self, mock_job_status):
        """
        Stale sources in this test means a job exists for the
        address being searched, and the job has been
        stopped, failed, or cancelled.
        Assert that retrieving an address with stale sources
        will add a job to the redis queue.
        """
        # set up test
        # create an existing job for the address that is to be searched
        job = self.queue.enqueue(
            "",
            job_id=self.test_addr
        )
        prev_created_at = job.created_at

        # mock the job's status to be stopped, failed, cancelled
        to_test = [
            rq.job.JobStatus.STOPPED,
            rq.job.JobStatus.FAILED,
            rq.job.JobStatus.CANCELED
        ]

        for status in to_test:
            # mock the status
            mock_job_status.return_value = status

            # call controller and make assertions
            stale, enqueued = self.controller.enqueue_if_stale(
                self.test_addr
            )
            self.assertTrue(stale)
            self.assertTrue(enqueued)

            # assert that a new job was added to the queue
            job = rq.job.Job.fetch(
                self.test_addr,
                connection=self.fake_redis
            )
            self.assertGreater(job.created_at, prev_created_at)
            prev_created_at = job.created_at

    def test_parent_job_runs_after_child_failure(self):
        """
        Assert that the parent job runs regardless of
        whether its children succeeded or failed.
        """
        # set up test
        # create a scraper job that will succeed
        will_succeed = PicklableMock()
        will_succeed.name = "scraper_one"  # pylint: disable=W0201
        will_succeed.run.return_value = None

        # create a scraper job that will fail
        will_fail = PicklableMock()
        will_fail.name = "scraper_two"  # pylint: disable=W0201
        will_fail.run.side_effect = RuntimeError("Failed.")

        # mock controller scrapers
        scrapers = [will_succeed, will_fail]
        with mock.patch(
            "nametags.jobs.controllers.scraper_jobs_to_run",
            scrapers
        ):
            # call controller
            controller = ScraperJobsController(
                redis_cursor=self.fake_redis,
                redis_queue=self.queue
            )
            controller.enqueue_if_stale(
                self.test_addr
            )

            # assert that one job failed, the other succeeded
            successful_job = rq.job.Job.fetch(
                f"{self.test_addr}_scraper_one",
                connection=self.fake_redis
            )
            failed_job = rq.job.Job.fetch(
                f"{self.test_addr}_scraper_two",
                connection=self.fake_redis
            )
            self.assertTrue(successful_job.is_finished)
            self.assertTrue(failed_job.is_failed)

            # assert that the parent job depends on the children
            parent_job = rq.job.Job.fetch(
                f"{self.test_addr}",
                connection=self.fake_redis
            )
            assert (successful_job.id in str(parent_job.dependency_ids[0])) \
                or (successful_job.id in str(parent_job.dependency_ids[1]))
            assert (failed_job.id in str(parent_job.dependency_ids[0])) \
                or (failed_job.id in str(parent_job.dependency_ids[1]))
            self.assertEqual(parent_job.allow_dependency_failures, 1)
