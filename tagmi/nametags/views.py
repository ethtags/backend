"""
Views for the nametags application.
"""
# std lib imports

# third party imports
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Case, IntegerField, Sum, When
from django.http import Http404
from rest_framework import generics, mixins
from rest_framework.response import Response
import django_rq
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

        # sort the queryset by descending net upvote count
        # (upvotes minus downvotes) from greatest to least
        queryset = queryset.order_by("-net_upvotes", "-created")

        return queryset

    def get(self, request, *args, **kwargs):
        address = kwargs['address']

        # check for last refresh of sources on the given address
        job_class = django_rq.jobs.get_job_class()

        try:
            # get job for given address
            job = job_class.fetch(address, redis_cursor)
            status = job.get_status(refresh=True)

            # job status is failed, stopped, cancelled
            # requeue the job, set stale to True
            if job.is_failed is True \
                or job.is_stopped is True \
                or job.is_canceled is True:
                # TODO set stale to True
                job = long_running_func.delay(job_id=address) 
                print("created job: ", job)

            # job status is queued, started, deferred
            # do not requeue the job, set stale to True 
            elif job.is_queued is True \
                or job.is_started is True \
                or job.is_deferred is True:
                # TODO set stale to True
                print("job is in progress, set stale to True")

            # job status is finished (successful)
            # do not queue the job, set stale to False 
            elif job.is_finished is True:
                # TODO set stale to false
                print("job is finished, set stale to False") 

            else:
                raise Exception(f"Job {job} is in an undefined state, investigate.")

        # job cannot be found therefore it is stale, create new job 
        except rq.exceptions.NoSuchJobError:
            # TODO set stale to True
            job = long_running_func.delay(job_id=address) 
            print("created job: ", job)
            print("set stale to True")

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
