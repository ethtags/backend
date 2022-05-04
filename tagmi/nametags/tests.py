"""
Module containing tests for the nametags application.
"""
# std lib imports

# third part imports
from rest_framework import status
from rest_framework.test import APITestCase

# our imports
from .models import Address, Tag, Vote


class NametagsTests(APITestCase):
    """
    Represents a Django class test case.
    """

    def setUp(self):
        """
        Runs once before each test.
        """
        self.addresses = [
            "0x4622BeF7d6C5f7f1ACC479B764688DC3E7316d68",
            "0x41329485877D12893bC4ef88A9208ee5cB5f5525"
        ]

    def test_create_new_nametag(self):
        """
        Assert that a new nametag is created for an address
        if that nametag does not already exist.
        """
        # set up test
        url = f"/{self.addresses[0]}/tags/"
        tag_value = "Test Address One"
        data = {'nametag': tag_value}

        # make request
        response = self.client.post(url, data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Address created
        self.assertEqual(Address.objects.count(), 1)
        self.assertIsNotNone(
            Address.objects.get(publickey=self.addresses[0].lower())
        )

        # Tag created
        self.assertEqual(Tag.objects.count(), 1)
        tag_one = Tag.objects.get(id=1)
        self.assertEqual(
            tag_one.nametag,
            tag_value
        )

        # Vote created
        self.assertEqual(Vote.objects.count(), 1)
        vote_one = Vote.objects.get(id=1)
        self.assertEqual(
            vote_one.tag,
            tag_one
        )
        self.assertEqual(
            vote_one.value,
            True  # upvote
        )
