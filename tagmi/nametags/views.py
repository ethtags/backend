"""
Views for the nametags application.
"""
# std lib imports

# third party imports
from rest_framework import generics

# our imports
from .models import Tag, Vote
from . import serializers


class TagList(generics.ListCreateAPIView):
    """ View that allows listing and creating Tags. """

    serializer_class = serializers.TagSerializer

    def get_queryset(self):
        queryset = Tag.objects.filter(address=self.kwargs['address'].lower())
        return queryset


class VoteList(generics.ListCreateAPIView):
    """ View that allows listing and creating Votes. """

    serializer_class = serializers.VoteSerializer

    def get_queryset(self):
        queryset = Vote.objects.filter(tag=self.kwargs['tag_id'])
        return queryset
