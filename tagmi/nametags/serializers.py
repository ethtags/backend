"""
Module containing serializers for the different models of the nametags app.
"""
# std lib imports

# third party imports
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

# our imports
from .constants import NAMETAG_FORMAT
from .models import Address, Tag, Vote
from .utils import create_session_if_dne


class VoteSerializer(serializers.ModelSerializer):
    """ Serializer for the Tag model. """

    class Meta:
        model = Vote
        fields = [
            "upvotes",
            "downvotes",
            "userVoted",
            "userVoteChoice",
            "value"
        ]

    value = serializers.NullBooleanField(write_only=True)
    upvotes = serializers.SerializerMethodField('get_upvotes_count')
    downvotes = serializers.SerializerMethodField('get_downvotes_count')
    userVoted = serializers.SerializerMethodField('get_user_voted')
    userVoteChoice = serializers.SerializerMethodField('get_user_vote_choice')

    def get_user_voted(self, _):
        """
        Returns True/False if the requestor has voted before.
        """
        session_id = self.context['request'].session.session_key

        # VoteSerializer is nested and its parent is
        # a ListSerializer or TagSerialzier, e.g.
        #   - when doing a GET for a list of nametags
        #   - when doing a POST for a nametag
        if isinstance(self.root, (
            serializers.ListSerializer,
            TagSerializer
        )):
            tag = self.parent.instance

        # VoteSerializer is not nested, e.g.
        #   - when doing a GET for the votes of a specific nametag
        else:
            tag = self.context['view'].kwargs.get("tag_id", None)

        return Vote.objects.filter(
            tag=tag,
            created_by_session_id=session_id
        ).exists()

    def get_user_vote_choice(self, _):
        """
        Returns True/False if the requestor has upvoted/downvoted.
        Returns None if the requestor has not voted.
        """
        session_id = self.context['request'].session.session_key

        # VoteSerializer is nested and its parent is
        # a ListSerializer or TagSerialzier, e.g.
        #   - when doing a GET for a list of nametags
        #   - when doing a POST for a nametag
        if isinstance(self.root, (
            serializers.ListSerializer,
            TagSerializer
        )):
            tag = self.parent.instance

        # VoteSerializer is not nested, e.g.
        #   - when doing a GET for the votes of a specific nametag
        else:
            tag = self.context['view'].kwargs.get("tag_id", None)

        user_vote = Vote.objects.filter(
            tag=tag,
            created_by_session_id=session_id
        ).first()

        return getattr(user_vote, "value", None)

    def get_upvotes_count(self, _):
        """
        Return the total number of upvotes for a given nametag.
        """
        # VoteSerializer is nested and its parent is
        # a ListSerializer or TagSerialzier, e.g.
        #   - when doing a GET for a list of nametags
        #   - when doing a POST for a nametag
        if isinstance(self.root, (
            serializers.ListSerializer,
            TagSerializer
        )):
            tag = self.parent.instance

        # VoteSerializer is not nested, e.g.
        #   - when doing a GET for the votes of a specific nametag
        else:
            tag = self.context['view'].kwargs.get("tag_id", None)

        return Vote.objects.filter(tag=tag, value=True).count()

    def get_downvotes_count(self, _):
        """
        Return the total number of downvotes for a given nametag.
        """
        # VoteSerializer is nested and its parent is
        # a ListSerializer or TagSerialzier, e.g.
        #   - when doing a GET for a list of nametags
        #   - when doing a POST for a nametag
        if isinstance(self.root, (
            serializers.ListSerializer,
            TagSerializer
        )):
            tag = self.parent.instance

        # VoteSerializer is not nested, e.g.
        #   - when doing a GET for the votes of a specific nametag
        else:
            tag = self.context['view'].kwargs.get("tag_id", None)

        return Vote.objects.filter(tag=tag, value=False).count()

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

    class Meta:
        model = Tag
        fields = [
            "id", "nametag", "votes", "createdByUser", "created", "source"
        ]

    votes = VoteSerializer(
        read_only=True
    )
    createdByUser = serializers.SerializerMethodField('get_created_by_user')

    def get_created_by_user(self, obj):
        """
        Returns True if the requestor created the nametag.
        Returns False otherwise.
        """
        session_key = self.context['request'].session.session_key

        if obj.created_by_session_id == session_key:
            return True

        return False

    def validate_nametag(self, value):
        """
        Returns value if nametag passes validation.
        Raises serializers.ValidationError otherwise.
        Nametag must conform to:
            - A-Z, a-z, 0-9, -, _, whitespace, comma, period, apostrophe.
        """
        if not NAMETAG_FORMAT.match(value):
            raise serializers.ValidationError(
                "Nametag can only contain A-Z a-z 1-9 ' . ,"
            )

        return value

    def create(self, validated_data):
        # get address from the URL
        address_kwarg = self.context.get("view").kwargs["address"].lower()

        # get or create Address
        address, _ = Address.objects.get_or_create(
            pubkey=address_kwarg
        )

        # create Nametag
        request = self.context.get("view").request
        create_session_if_dne(request)
        tag = Tag.objects.create(
            nametag=validated_data.pop("nametag"),
            address=address,
            created_by_session_id=request.session.session_key
        )

        # automatically upvote the nametag since user wanted to create it
        tag.votes.create(
            value=True,
            created_by_session_id=request.session.session_key
        )

        return tag

    def to_representation(self, instance):
        """
        Overrides to_representation.
        Adds an instance attribute to the TagSerializer so that its child
        serializers can access specific instances when TagSerializer is a
        ListSerializer, i.e. many=True.
        """
        self.instance = instance
        return super().to_representation(instance)


class AddressSerializer(serializers.ModelSerializer):
    """ Serializer for the Address model. """

    class Meta:
        model = Address
        fields = [
            "nametags", "sourcesAreStale"
        ]

    nametags = TagSerializer(
        source="tags",
        many=True,
        read_only=True
    )

    sourcesAreStale = serializers.BooleanField(
        source="sources_are_stale",
        read_only=True
    )
