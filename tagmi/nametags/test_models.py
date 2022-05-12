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
            pubkey=self.test_addrs[0]
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


class AddressTests(TestCase):
    """ Class that tests the Address model. """

    def setUp(self):
        """
        Runs before each test.
        """
        self.addr = "0x4622BeF7d6C5f7f1ACC479B764688DC3E7316d68"

    def test_address_lowercase(self):
        """
        Assert that an address is saved to the database as
        lowercase even if it is passed in as mixed or uppercase.
        """
        Address.objects.create(pubkey=self.addr)

        address = Address.objects.first()
        self.assertEqual(
            address.pubkey,
            self.addr.lower()
        )

    def test_address_invalid_length(self):
        """
        Assert that a ValidationError is raised if an
        address is not 42 characters long.
        """
        short = self.addr[0:41]

        with self.assertRaises(ValidationError) as error:
            Address.objects.create(pubkey=short)

        err_msg = error.exception.messages[0]
        self.assertIn("must be 42 characters", err_msg)

        too_long = f"{self.addr}A"

        with self.assertRaises(ValidationError) as error:
            Address.objects.create(pubkey=too_long)

        err_msg = error.exception.messages[0]
        self.assertIn("at most 42 characters", err_msg)

    def test_address_no_0x(self):
        """
        Assert that a ValidationError is raised if an
        address does not start with 0x.
        """
        bad_prefix = f"0z{self.addr[2:42]}"

        with self.assertRaises(ValidationError) as error:
            Address.objects.create(pubkey=bad_prefix)

        err_msg = error.exception.messages[0]
        self.assertIn("must start with 0x", err_msg)

    def test_address_bad_hex(self):
        """
        Assert that a ValidationError is raised if an
        address has invalid hex after the 0x.
        """
        bad_hex = f"{self.addr[0:41]}z"

        with self.assertRaises(ValidationError) as error:
            Address.objects.create(pubkey=bad_hex)

        err_msg = error.exception.messages[0]
        self.assertIn("must be hex", err_msg)
