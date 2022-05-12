"""
Module containing serializers for the different models of the nametags app.
"""
# std lib imports

# third party imports
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied

# our imports
from .models import Address, Tag, Vote
from .utils import create_session_if_dne


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

        # create sesion for the user if it does not exist
        request = self.context.get("view").request
        create_session_if_dne(request)

        # do not allow a user to vote on the same nametag twice
        if Vote.objects.filter(
            tag=tag,
            created_by_session_id=request.session.session_key
        ).exists():
            raise ValidationError("User has already voted on this nametag.")

        # create vote
        vote = Vote.objects.create(
            tag=tag,
            value=self.validated_data["value"],
            created_by_session_id=request.session.session_key
        )

        return vote

    def update(self, instance, validated_data):

        # only vote creator can update the vote
        session_id = self.context.get("view").request.session.session_key
        if instance.created_by_session_id != session_id:
            raise PermissionDenied("Only vote creator can update vote.")

        # update the vote
        instance.value = validated_data.get("value", instance.value)
        instance.save()

        return instance


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
        request = self.context.get("view").request
        create_session_if_dne(request)
        tag, _ = Tag.objects.get_or_create(
            nametag=validated_data.pop("nametag"),
            address=address,
            created_by_session_id=request.session.session_key
        )

        # automatically upvote the nametag since user wanted to create it
        Vote.objects.create(
            value=True,
            tag=tag,
            created_by_session_id=request.session.session_key
        )

        return tag
