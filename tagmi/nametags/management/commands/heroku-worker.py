# pylint: disable=invalid-name
"""
Django command that runs a worker which connects to and
listens on the redis instance hosted at environment variable REDIS_URL.
"""
# std lib imports
import urllib.parse

# third party imports
from django.conf import settings
from django.core.management.base import BaseCommand
from redis import Redis
from rq import Queue, Connection
from rq.worker import HerokuWorker as Worker

# our imports


listen = ['default']
redis_url = settings.REDIS_URL
url = urllib.parse.urlparse(redis_url)


class Command(BaseCommand):
    """
    Runs RQ workers on specified queues. Note that all queues passed into a
    single rqworker command must share the same connection.

    Example usage:
    python manage.py heroku-worker
    """

    def handle(self, *args, **options):
        """ Main entrypoint into the django command. """

        conn = Redis(
            host=url.hostname, port=url.port, db=0, password=url.password
        )

        with Connection(conn):
            worker = Worker(map(Queue, listen))
            worker.work()
