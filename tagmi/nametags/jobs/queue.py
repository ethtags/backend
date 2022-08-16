""" Module containing subclass of RQ's Queue. To be used for queueing jobs. """
# std lib imports

# third party imports
from django.conf import settings
import rq

# our imports


class Queue(rq.Queue):
    """ Subclass of RQ's Queue. """

    # pylint: disable=too-many-arguments,too-many-locals
    def enqueue_call(self, func, args=None, kwargs=None, timeout=None,
                     result_ttl=None, ttl=None, failure_ttl=None,
                     description=None, depends_on=None, job_id=None,
                     at_front=False, meta=None, retry=None, on_success=None,
                     on_failure=None, pipeline=None):
        """
        Overrides base class method to include our settings.
        Creates a job to represent the delayed function call and enqueues it.
        """
        # fallback to our settings
        if result_ttl is None:
            result_ttl = settings.RQ["DEFAULT_RESULT_TTL"]

        # call parent method
        return super().enqueue_call(func=func, args=args, kwargs=kwargs,
                                    timeout=timeout, result_ttl=result_ttl,
                                    ttl=ttl, failure_ttl=failure_ttl,
                                    description=description,
                                    depends_on=depends_on, job_id=job_id,
                                    at_front=at_front, meta=meta, retry=retry,
                                    on_success=on_success,
                                    on_failure=on_failure, pipeline=pipeline)
