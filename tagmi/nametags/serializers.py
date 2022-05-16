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
        fields = ["upvotes", "downvotes", "userVoteChoice", "value"]

    value = serializers.BooleanField(write_only=True)
    upvotes = serializers.SerializerMethodField('get_upvotes_count')
    downvotes = serializers.SerializerMethodField('get_downvotes_count')
    userVoteChoice = serializers.SerializerMethodField('get_user_vote_choice')

    def get_user_vote_choice(self, obj):
        """
        Returns the Vote value if the Vote was created by the requestor.
        Returns None if the Vote was not created by the requestor.
        """
        session_id = self.context['request'].session.session_key
        tag_id = self.context['view'].kwargs.get("tag_id", None)

        # TODO how to handle listing of nametags when there is no tag_id

        # handle GET votes case
        user_vote = Vote.objects.filter(
            tag=tag_id,
            created_by_session_id=session_id
        ).first()
        if user_vote is None:
            return None
        
        return user_vote.value

    def get_upvotes_count(self, obj):
        # TODO how to handle listing of nametags when there is no tag_id
        tag_id = self.context['view'].kwargs.get("tag_id", None)
        return Vote.objects.filter(tag=tag_id, value=True).count()

    def get_downvotes_count(self, obj):
        # TODO how to handle listing of nametags when there is no tag_id
        tag_id = self.context['view'].kwargs.get("tag_id", None)
        return Vote.objects.filter(tag=tag_id, value=False).count()

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
        tag = Tag.objects.create(
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
