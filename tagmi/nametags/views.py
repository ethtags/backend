"""
Views for the nametags application.
"""
# std lib imports

# third party imports
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

    def get_object(self, *args, **kwargs):
        """ Returns a vote instance that was created by the user, or 404. """
        session_key = self.request.session.session_key
        self.kwargs["tag"] = self.kwargs["tag_id"]
        self.kwargs["created_by_session_id"] = session_key
        return super().get_object(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        queryset = Vote.objects.none()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # delete the instance
        instance = self.get_object()
        instance.delete()

        # return the updated representation of votes
        queryset = Vote.objects.none()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)


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
