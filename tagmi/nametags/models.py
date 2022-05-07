"""
Module containing application objects that will be mapped to database tables.
"""
# std lib imports

# third party imports
from django.core.exceptions import ValidationError
from django.db import models

# our imports


class Address(models.Model):
    """ Represents an Ethereum based address. """

    pubkey = models.CharField(
        max_length=42,
        primary_key=True,
        blank=False,
        editable=False
    )

    def clean(self, *args, **kwargs):
        """ Validation of custom business logic before. """

        # make sure public address is 42 characters
        if len(self.pubkey) != 42:
            raise ValidationError(
                "pubkey must be 42 characters"
            )

        # save public address as lowercase
        self.pubkey = self.pubkey.lower()

        # assert public address starts with 0x
        if self.pubkey[0:2] != "0x":
            raise ValidationError("pubkey must start with 0x")

        # assert pubkey is hex
        try:
            int(self.pubkey[2:42], 16)
        except ValueError as value_error:
            raise ValidationError(
                "pubkey must be hex after the '0x'"
            ) from value_error

    def save(self, *args, **kwargs):
        """ Custom business logic on write. """

        self.full_clean()
        super().save(*args, **kwargs)


class Tag(models.Model):
    """ Represents a nametag related to an address and can be voted on. """

    nametag = models.CharField(
        max_length=60,
        blank=False,
    )
    address = models.ForeignKey(
        to=Address,
        on_delete=models.CASCADE
    )

    def validate_unique(self, *args, **kwargs):
        """ Validate unique constraints. """

        super().validate_unique(*args, **kwargs)

        # check for existing nametag
        exists = Tag.objects.filter(
            address=self.address,
            nametag=self.nametag
        )
        if len(exists) > 0:
            raise ValidationError("Nametag already exists for that address.")

    def save(self, *args, **kwargs):
        """ Custom business logic on write. """

        self.full_clean()
        super().save(*args, **kwargs)


class Vote(models.Model):
    """ Represents a vote for a nametag of an address. """

    # upvote is True, downvote is False, no vote is null
    value = models.BooleanField(null=True)
    tag = models.ForeignKey(
        to=Tag,
        on_delete=models.CASCADE
    )
