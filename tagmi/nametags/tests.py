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

    def test_create_new_nametag_address_dne(self):
        """
        Assert that a new address is created when it does not exist.
        Assert that a new nametag is created for the new address.
        Assert that an upvote is created for the new nametag.
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
            Address.objects.get(pubkey=self.addresses[0].lower())
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

    def test_create_new_nametag_address_exists(self):
        """
        Assert that a new nametag is created for an existing address.
        Assert that an upvote is created for the new nametag.
        """
        # set up test
        url = f"/{self.addresses[0]}/tags/"
        tag_value = "Test Address One"
        data = {'nametag': tag_value}
        Address.objects.create(
            pubkey=self.addresses[0]
        )

        # assert that address count is 1
        self.assertEqual(Address.objects.count(), 1)

        # make request
        response = self.client.post(url, data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # no new address created, count should still be 1
        self.assertEqual(Address.objects.count(), 1)

        # Tag created
        self.assertEqual(Tag.objects.count(), 1)
        tag_one = Tag.objects.get(id=1)
        self.assertEqual(
            tag_one.nametag,
            tag_value
        )
        self.assertEqual(
            tag_one.address.pubkey,
            self.addresses[0].lower()
        )

        # Vote created
        self.assertEqual(Vote.objects.count(), 1)

    def test_create_new_nametag_exists(self):
        """
        Assert that a new nametag is NOT created if a nametag
        with the same value already exists for a given address.
        Assert that a 201 is returned with the existing nametag.
        Assert that an upvote is created for the existing nametag.
        """
        # set up test
        tag_value = "Test Address One"
        url = f"/{self.addresses[0]}/tags/"
        data = {'nametag': tag_value}
        response = self.client.post(url, data)  # create tag
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # make request
        # create the same nametag for the same address
        response = self.client.post(url, data)  # create same tag

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nametag"], tag_value)

        # assert that no new Tag was created
        tags = Tag.objects.all()
        self.assertEqual(len(tags), 1)

        # assert that an upvote was created for the existing Tag
        votes = Vote.objects.filter(tag=tags[0])
        self.assertEqual(len(votes), 2)
        self.assertEqual(votes[0].value, True)
        self.assertEqual(votes[1].value, True)

    def test_create_nametag_exists_diff_address(self):
        """
        Assert that a new nametag is created for a given address if a nametag
        with the same value already exists for a different address.
        """
        # set up test
        # create a nametag for address one
        tag_value = "Test Address One"
        data = {'nametag': tag_value}
        url = f"/{self.addresses[0]}/tags/"
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # make request
        # create a nametag for address two
        url = f"/{self.addresses[1]}/tags/"
        response = self.client.post(url, data)

        # make assertions
        # assert that the response was a 201 with the new tag created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nametag"], tag_value)

        # assert that both addresses have a nametag with the same value
        tags_addrs_one = Tag.objects.filter(
            address=self.addresses[0].lower(),
            nametag=tag_value
        )
        self.assertEqual(len(tags_addrs_one), 1)

        tags_addrs_two = Tag.objects.filter(
            address=self.addresses[1].lower(),
            nametag=tag_value
        )
        self.assertEqual(len(tags_addrs_two), 1)

    def test_list_nametags(self):
        """
        Assert that a list of all nametags related to an address are returned.
        """
        # set up test
        # create nametags for addresses one and two
        url = f"/{self.addresses[0]}/tags/"
        data = {'nametag': "Address One Nametag One"}
        self.client.post(url, data)

        data = {'nametag': "Address One Nametag Two"}
        self.client.post(url, data)

        url = f"/{self.addresses[1]}/tags/"
        data = {'nametag': "Address Two Nametag One"}
        self.client.post(url, data)

        # make request
        # list nametags for address one
        url = f"/{self.addresses[0]}/tags/"
        response = self.client.get(url, data)

        # make assertions
        # assert that the response was a 200
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(
            response.data[0]["nametag"],
            "Address One Nametag One"
        )
        self.assertEqual(
            response.data[1]["nametag"],
            "Address One Nametag Two"
        )

        # list nametags for address two
        url = f"/{self.addresses[1]}/tags/"
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["nametag"],
            "Address Two Nametag One"
        )
