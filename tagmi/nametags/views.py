"""
Views for the nametags application.
"""
# std lib imports

# third party imports
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Value
from django.http import Http404
from rest_framework import generics, mixins, status
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.response import Response

# our imports
from .constants import ADDRESS_FORMAT
from .jobs.controllers import ScraperJobsController
from .models import Address, Tag, Vote
from .utils import order_nametags_queryset
from . import serializers


class AddressRetrieve(generics.RetrieveAPIView):
    """ View that allows retrieving addresses. """

    serializer_class = serializers.AddressSerializer
    sources_are_stale = False
    address = None

    def get_object(self):
        """
        Returns the object the view is displaying.
        """
        try:
            filter_kwargs = {"pubkey": self.address}
            queryset = self.get_queryset()
            obj = queryset.get(**filter_kwargs)

            # May raise a permission denied
            self.check_object_permissions(self.request, obj)

            return obj

        except Address.DoesNotExist as exc:
            raise NotFound() from exc

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves an object and returns its serialized
        representation in a Response.
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        # return 404 and body indicating whether sources are stale
        except NotFound:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={"sourcesAreStale": self.sources_are_stale}
            )

    def get_queryset(self):
        """
        Returns the queryset used for retrieving addresses.
        """
        queryset = Address.objects.filter(pubkey=self.address)

        # annotate whether the address sources are stale
        # self.sources_are_stale is set in the get method below
        queryset = queryset.annotate(
            sources_are_stale=Value(self.sources_are_stale)
        )

        return queryset

    def get(self, request, *args, **kwargs):

        # return 400 bad request if address is not in desired format
        self.address = kwargs["address"].lower()
        if not ADDRESS_FORMAT.match(self.address):
            raise ParseError("Invalid address format given")

        # handle stale sources for address
        jobs_controller = ScraperJobsController()
        is_stale, _ = jobs_controller.enqueue_if_stale(self.address)
        self.sources_are_stale = is_stale

        return self.retrieve(request, *args, **kwargs)


class TagListCreate(generics.ListCreateAPIView):
    """ View that allows listing and creating Tags. """

    serializer_class = serializers.TagSerializer

    def get_queryset(self):
        """
        Returns the queryset used for listing tags.
        """
        # query for all tags matching the address given in the url
        queryset = Tag.objects.filter(address=self.kwargs["address"].lower())

        # sort the queryset by descending net upvote count
        queryset = order_nametags_queryset(queryset)

        return queryset


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
