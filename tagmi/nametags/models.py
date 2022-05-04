"""
Module containing application objects that will be mapped to database tables.
"""
# std lib imports

# third party imports
from django.db import models

# our imports


class Address(models.Model):
    """ Represents an Ethereum based address. """

    publickey = models.CharField(
        max_length=42,
        primary_key=True,
        blank=False,
        editable=False
    )

    def save(self, *args, **kwargs):
        """ Custom business logic on write. """

        # make sure public address is 42 characters
        assert len(self.publickey) == 42

        # save public address as lowercase
        self.publickey = self.publickey.lower()

        # assert public address starts with 0x
        assert self.publickey[0:2] == "0x"

        # raise ValueError if the 40 chars after 0x are not hex
        int(self.publickey[2:42], 16)

        # call save
        super().save(*args, **kwargs)


class Tag(models.Model):
    """ Represents a nametag related to an address and can be voted on. """

    nametag = models.CharField(
        max_length=60,
        unique=True,
        blank=False,
    )
    address = models.ForeignKey(
        to=Address,
        on_delete=models.CASCADE
    )


class Vote(models.Model):
    """ Represents a vote for a nametag of an address. """

    # upvote is True, downvote is False, no vote is null
    value = models.BooleanField(null=True)
    tag = models.ForeignKey(
        to=Tag,
        on_delete=models.CASCADE
    )
