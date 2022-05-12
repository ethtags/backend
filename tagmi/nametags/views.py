"""
Views for the nametags application.
"""
# std lib imports

# third party imports
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

# our imports
from .models import Tag, Vote
from . import serializers


class TagListCreate(generics.ListCreateAPIView):
    """ View that allows listing and creating Tags. """

    serializer_class = serializers.TagSerializer

    def get_queryset(self):
        queryset = Tag.objects.filter(address=self.kwargs['address'].lower())
        return queryset


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
