"""
Module containing serializers for the different models of the nametags app.
"""
# std lib imports

# third party imports
from rest_framework import serializers

# our imports
from .models import Address, Tag, Vote


class VoteSerializer(serializers.ModelSerializer):
    """ Serializer for the Tag model. """

    class Meta:
        model = Vote
        fields = ["value"]

    def create(self, validated_data):
        # get Tag id from the URL
        tag_id = self.context.get("view").kwargs["tag_id"]

        # get Tag
        tag = Tag.objects.get(id=tag_id)

        # create Vote
        vote = Vote.objects.create(
            tag=tag,
            value=self.validated_data["value"]
        )

        return vote


class TagSerializer(serializers.ModelSerializer):
    """ Serializer for the Tag model. """

    votes = VoteSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Tag
        fields = ["id", "nametag", "votes"]

    def create(self, validated_data):
        # get address from the URL
        address_kwarg = self.context.get("view").kwargs["address"].lower()

        # get or create Address
        address, _ = Address.objects.get_or_create(
            pubkey=address_kwarg
        )

        # get or create Nametag
        tag, _ = Tag.objects.get_or_create(
            nametag=validated_data.pop("nametag"),
            address=address
        )

        # automatically upvote the nametag since user wanted to create it
        Vote.objects.create(value=True, tag=tag)

        return tag
