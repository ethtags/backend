"""
Module containing serializers for the different models of the nametags app.
"""
# std lib imports

# third party imports
from rest_framework import serializers

# our imports
from .models import Address, Tag, Vote


class TagSerializer(serializers.ModelSerializer):
    """ Serializer for the Tag model. """

    class Meta:
        model = Tag
        fields = ["nametag"]

    def create(self, validated_data):
        # get address from the URL
        address_kwarg = self.context.get("view").kwargs["address"].lower()

        # get or create Address
        address, _ = Address.objects.get_or_create(
            publickey=address_kwarg
        )

        # get or create Nametag
        tag, _ = Tag.objects.get_or_create(
            nametag=validated_data.pop("nametag"),
            address=address
        )

        # automatically upvote the nametag since user wanted to create it
        Vote.objects.create(value=True, tag=tag)

        return tag
