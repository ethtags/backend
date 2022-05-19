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

    def get_user_vote_choice(self, _):
        """
        Returns True/False if the requestor has upvoted/downvoted.
        Returns None if the requestor has not voted.
        """
        session_id = self.context['request'].session.session_key
        tag_id = self.context['view'].kwargs.get("tag_id", None)

        # VoteSerializer is nested and its parent is a ListSerializer, e.g.
        #   - when doing a GET for a list of nametags
        if isinstance(self.root, serializers.ListSerializer):
            tag = self.parent.instance
            user_vote = Vote.objects.filter(
                tag=tag,
                created_by_session_id=session_id
            ).first()

            return getattr(user_vote, "value", None)

        # VoteSerializer is not nested, e.g.
        #   - when doing a GET for the votes of a specific nametag
        user_vote = Vote.objects.filter(
            tag=tag_id,
            created_by_session_id=session_id
        ).first()

        return getattr(user_vote, "value", None)

    def get_upvotes_count(self, _):
        """
        Return the total number of upvotes for a given nametag.
        """
        # VoteSerializer is nested and its parent is a ListSerializer, e.g.
        #   - when doing a GET for a list of nametags
        if isinstance(self.root, serializers.ListSerializer):
            tag = self.parent.instance
            return Vote.objects.filter(
                tag=tag.id,
                value=True
            ).count()

        # VoteSerializer is not nested, e.g.
        #   - when doing a GET for the votes of a specific nametag
        tag_id = self.context['view'].kwargs.get("tag_id", None)

        return Vote.objects.filter(tag=tag_id, value=True).count()

    def get_downvotes_count(self, _):
        """
        Return the total number of downvotes for a given nametag.
        """
        # VoteSerializer is nested and its parent is a ListSerializer, e.g.
        #   - when doing a GET for a list of nametags
        if isinstance(self.root, serializers.ListSerializer):
            tag = self.parent.instance
            return Vote.objects.filter(
                tag=tag.id,
                value=False
            ).count()

        # VoteSerializer is not nested, e.g.
        #   - when doing a GET for the votes of a specific nametag
        tag_id = self.context['view'].kwargs.get("tag_id", None)
        return Vote.objects.filter(tag=tag_id, value=False).count()

    def create(self, validated_data):
        """
        Create a Vote and return the created object.
        """
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
        """
        Update an existing vote.
        """
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

    def to_representation(self, instance):
        """
        Overrides the parent to_representation.
        Adds an _instance attribute to the TagSerializer so that its child
        serializers can access specific instances TagSerializer is a
        ListSerializer, i.e. many=True.
        """
        self.instance = instance
        return super().to_representation(instance)
