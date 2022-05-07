"""
Module that tests the nametags models.
"""
# std lib imports

# third party imports
from django.core.exceptions import ValidationError
from django.test import TestCase

# our imports
from .models import Address, Tag


class TagTests(TestCase):
    """ Class that tests the Tag model. """

    def setUp(self):
        """
        Runs before each test.
        """
        self.test_addrs = [
            "0x4622BeF7d6C5f7f1ACC479B764688DC3E7316d68",
            "0x41329485877D12893bC4ef88A9208ee5cB5f5525"
        ]

    def test_tag_unique_same_address(self):
        """
        Assert that a Tag cannot be created if one already exists
        with the same nametag and address.
        """
        # prepare test
        tag_value = "Tag One"
        address = Address.objects.create(
            publickey=self.test_addrs[0]
        )
        Tag.objects.create(
            address=address,
            nametag=tag_value
        )

        # assert that creating new nametag with
        # same address and value raises an exception
        with self.assertRaises(ValidationError):
            Tag.objects.create(
                address=address,
                nametag=tag_value
            )
