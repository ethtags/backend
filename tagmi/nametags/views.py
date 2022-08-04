"""
Views for the nametags application.
"""
# std lib imports

# third party imports
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Case, IntegerField, Sum, Value, When
from django.http import Http404
from rest_framework import generics, mixins
from rest_framework.response import Response
from rq.job import JobStatus
import redis
import rq

# our imports
from .jobs.simple import long_running_func
from .models import Tag, Vote
from . import serializers


redis_cursor = redis.Redis()


class TagListCreate(generics.ListCreateAPIView):
    """ View that allows listing and creating Tags. """

    serializer_class = serializers.TagSerializer
    source_is_stale = False

    def get_queryset(self):
        """
        Returns the queryset used for listing tags.
        """
        # query for all tags matching the address given in the url
        queryset = Tag.objects.filter(address=self.kwargs["address"].lower())

        # annotate the tags so that they can be sorted by net upvote count
        # https://docs.djangoproject.com/en/4.0/topics/db/aggregation/
        # https://docs.djangoproject.com/en/4.0/ref/models/conditional-expressions/
        queryset = queryset.annotate(
            net_upvotes=Sum(
                Case(
                    When(votes__value=True, then=1),
                    When(votes__value=False, then=-1),
                    When(votes__value=None, then=0),
                    output_field=IntegerField()
                )
            )
        )

        # annotate whether the source is stale
        queryset = queryset.annotate(
            source_is_stale=Value(self.source_is_stale)
        )

        # sort the queryset by descending net upvote count
        # (upvotes minus downvotes) from greatest to least
        queryset = queryset.order_by("-net_upvotes", "-created")

        return queryset

    def get(self, request, *args, **kwargs):
        address = kwargs['address']
        address = address.lower()

        # handle stale sources
        try:
            # get job for given address
            job = rq.job.Job.fetch(address, redis_cursor)
            status = job.get_status(refresh=True)

            # job status is failed, stopped, cancelled
            # requeue the job, set stale to True
            if status in [
                JobStatus.FAILED,
                JobStatus.STOPPED,
                JobStatus.CANCELED
            ]:
                redis_queue = rq.Queue(connection=redis_cursor)
                job = redis_queue.enqueue(long_running_func, job_id=address)
                self.source_is_stale = True

            # job status is queued, started, deferred
            # do not requeue the job, set stale to True
            elif status in [
                JobStatus.QUEUED,
                JobStatus.STARTED,
                JobStatus.DEFERRED
            ]:
                self.source_is_stale = True

            # job status is finished (successful)
            # do not queue the job, set stale to False
            elif status in [JobStatus.FINISHED]:
                self.source_is_stale = False

            else:
                raise Exception(
                    f"Job {job} is in an undefined state, investigate."
                )

        # job cannot be found therefore it is stale
        # create new job, mark results as stale
        except rq.exceptions.NoSuchJobError:
            redis_queue = rq.Queue(connection=redis_cursor)
            job = redis_queue.enqueue(long_running_func, job_id=address)
            self.source_is_stale = True

        return self.list(request, *args, **kwargs)


class VoteCreateListUpdate(
        mixins.ListModelMixin,
        mixins.CreateModelMixin,
        mixins.UpdateModelMixin,
        generics.GenericAPIView):
    """ View that allows retrieving, creating, updating, deleting Votes. """

    serializer_class = serializers.VoteSerializer
    queryset = Vote.objects.all()
    lookup_url_kwarg = "tag_id"
    lookup_field = "tag"

    def get_object(self, *args, **kwargs):
        """
        Returns a vote instance that was created
        by the requestor, or 404.
        """
        # get session key for vote lookup
        session_key = self.request.session.session_key

        try:
            return Vote.objects.get(
                tag=self.kwargs["tag_id"],
                created_by_session_id=session_key
            )
        except ObjectDoesNotExist as dne:
            raise Http404 from dne

    def get(self, request, *args, **kwargs):
        """ Return the aggregate votes for the given nametag id. """

        queryset = Vote.objects.none()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """ Create a vote for the given nametag id. """

        return self.create(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        """
        Update the requestor's vote.
        Note that the check for whether a vote was
        created by the requestor is done in get_object.
        """

        return self.update(request, *args, **kwargs)
