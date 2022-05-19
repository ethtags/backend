"""
Views for the nametags application.
"""
# std lib imports

# third party imports
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework import generics, mixins
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

# our imports
from .models import Tag, Vote
from . import serializers


class TagListCreate(generics.ListCreateAPIView):
    """ View that allows listing and creating Tags. """

    serializer_class = serializers.TagSerializer

    def get_queryset(self):
        queryset = Tag.objects.filter(address=self.kwargs['address'].lower())
        return queryset


class VoteCreateListUpdateDelete(mixins.ListModelMixin,
                                 mixins.CreateModelMixin,
                                 mixins.UpdateModelMixin,
                                 mixins.DestroyModelMixin,
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

    def delete(self, request, *args, **kwargs):
        """
        Delete the requestor's vote.
        Note that the check for whether a vote was
        created by the requestor is done in get_object.
        """
        # get instance
        instance = self.get_object()

        # do delete
        instance.delete()

        # return the updated aggregate representation of votes
        return self.get(request, *args, **kwargs)


class VoteListCreate(generics.ListCreateAPIView):
    """ View that allows listing and creating Votes. """

    serializer_class = serializers.VoteSerializer
    queryset = Vote.objects.all()
    lookup_url_kwarg = "tag_id"


class VoteGetUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    """ View that allows listing and creating Votes. """

    serializer_class = serializers.VoteSerializer
    queryset = Vote.objects.all()
    lookup_url_kwarg = "vote_id"

    def destroy(self, request, *args, **kwargs):
        """
        View for handling HTTP DELETE.
        """
        vote = Vote.objects.get(id=self.kwargs["vote_id"])

        # only vote creator can delete the vote
        if request.session.session_key != vote.created_by_session_id:
            raise PermissionDenied("Only vote creator can delete vote.")

        # perform delete
        return super().destroy(request, *args, **kwargs)
