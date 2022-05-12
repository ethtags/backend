"""
Module containing tests for the nametags application.
TODO:
  # test only 1 vote allowed per user per nametag per address
  # test that ValidationErrors from the models return a 400 BAD REQUEST to the view instead of 500.
  # refactor tests
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
        self.test_addrs = [
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
        url = f"/{self.test_addrs[0]}/tags/"
        tag_value = "Test Address One"
        data = {'nametag': tag_value}

        # make request
        response = self.client.post(url, data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Address created
        self.assertEqual(Address.objects.count(), 1)
        self.assertIsNotNone(
            Address.objects.get(pubkey=self.test_addrs[0].lower())
        )

        # Tag created
        self.assertEqual(Tag.objects.count(), 1)
        tag_one = Tag.objects.get(id=1)
        self.assertEqual(
            tag_one.nametag,
            tag_value
        )
        self.assertEqual(
            tag_one.created_by_session_id,
            self.client.cookies.get("sessionid").value
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
        self.assertEqual(
            vote_one.created_by_session_id,
            self.client.cookies.get("sessionid").value
        )

    def test_create_new_nametag_address_exists(self):
        """
        Assert that a new nametag is created for an existing address.
        Assert that an upvote is created for the new nametag.
        """
        # set up test
        url = f"/{self.test_addrs[0]}/tags/"
        tag_value = "Test Address One"
        data = {'nametag': tag_value}
        Address.objects.create(
            pubkey=self.test_addrs[0]
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
            self.test_addrs[0].lower()
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
        url = f"/{self.test_addrs[0]}/tags/"
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
        Assert that a new nametag is created for a given address even
        if a nametag with the same value already exists for a
        different address.
        """
        # set up test
        # create a nametag for address one
        tag_value = "Test Address One"
        data = {'nametag': tag_value}
        url = f"/{self.test_addrs[0]}/tags/"
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # make request
        # create a nametag for address two
        url = f"/{self.test_addrs[1]}/tags/"
        response = self.client.post(url, data)

        # make assertions
        # assert that the response was a 201 with the new tag created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nametag"], tag_value)

        # assert that both addresses have a nametag with the same value
        tags_addrs_one = Tag.objects.filter(
            address=self.test_addrs[0].lower(),
            nametag=tag_value
        )
        self.assertEqual(len(tags_addrs_one), 1)

        tags_addrs_two = Tag.objects.filter(
            address=self.test_addrs[1].lower(),
            nametag=tag_value
        )
        self.assertEqual(len(tags_addrs_two), 1)

    def test_list_nametags(self):
        """
        Assert that a list of all nametags related to an address are returned.
        """
        # set up test
        # create nametags for addresses one and two
        url = f"/{self.test_addrs[0]}/tags/"
        data = {'nametag': "Address One Nametag One"}
        self.client.post(url, data)

        data = {'nametag': "Address One Nametag Two"}
        self.client.post(url, data)

        url = f"/{self.test_addrs[1]}/tags/"
        data = {'nametag': "Address Two Nametag One"}
        self.client.post(url, data)

        # make request
        # list nametags for address one
        url = f"/{self.test_addrs[0]}/tags/"
        response = self.client.get(url)

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
        url = f"/{self.test_addrs[1]}/tags/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["nametag"],
            "Address Two Nametag One"
        )

    def test_list_nametags_votes(self):
        """
        Assert that a list of votes is returned for each
        nametag in the list of nametags.
        """
        # set up test
        # create nametags for address one
        url = f"/{self.test_addrs[0]}/tags/"
        data = {'nametag': "Address One Nametag One"}
        self.client.post(url, data)
        data = {'nametag': "Address One Nametag Two"}
        self.client.post(url, data)

        # make request
        response = self.client.get(url)

        # make assertions
        # assert that votes exist for each created tag
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # two tags
        self.assertEqual(
            response.data[0]["votes"][0]["value"],
            True
        )
        self.assertEqual(
            response.data[1]["votes"][0]["value"],
            True
        )


class VoteTests(APITestCase):
    """
    Represents a Django class test case.
    """

    def setUp(self):
        """
        Runs once before each test.
        """
        self.test_addrs = [
            "0x4622BeF7d6C5f7f1ACC479B764688DC3E7316d68",
            "0x41329485877D12893bC4ef88A9208ee5cB5f5525"
        ]

    def test_upvote_nametag(self):
        """
        Assert that an upvote is created for the desired nametag.
        """
        # set up test
        # create nametag
        response = self.client.post(
            f"/{self.test_addrs[0]}/tags/",
            {"nametag": "Test Address One"}
        )
        tag_id = response.data["id"]

        # make request
        url = f"/{self.test_addrs[0]}/tags/{tag_id}/votes/"
        data = {"value": True}
        response = self.client.post(url, data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert the nametag now has two votes,
        # one from creation and a second from upvoting
        votes = Vote.objects.filter(tag=tag_id)
        self.assertEqual(len(votes), 2)

        # assert that both votes are upvotes
        self.assertEqual(votes[0].value, True)
        self.assertEqual(votes[1].value, True)
        self.assertEqual(
            votes[1].created_by_session_id,
            self.client.cookies.get("sessionid").value
        )

    def test_downvote_nametag(self):
        """
        Assert that a downvote is created for the desired nametag.
        """
        # set up test
        # create nametag
        response = self.client.post(
            f"/{self.test_addrs[0]}/tags/",
            {"nametag": "Test Address One"}
        )
        tag_id = response.data["id"]

        # make request
        url = f"/{self.test_addrs[0]}/tags/{tag_id}/votes/"
        data = {"value": False}
        response = self.client.post(url, data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert the nametag now has two votes,
        # one from creation and a second from downvoting
        votes = Vote.objects.filter(tag=tag_id)
        self.assertEqual(len(votes), 2)

        # assert that one vote is an upvote and the other is a downvote
        self.assertEqual(votes[0].value, True)
        self.assertEqual(votes[1].value, False)
        self.assertEqual(
            votes[1].created_by_session_id,
            self.client.cookies.get("sessionid").value
        )

    def test_post_multiple_votes_nametag(self):
        """
        Assert that an attempt to post in multiple votes for
        a nametag in one request returns a 400 BAD REQUEST.
        """
        # set up test
        # create nametag
        response = self.client.post(
            f"/{self.test_addrs[0]}/tags/",
            {"nametag": "Test Address One"}
        )
        tag_id = response.data["id"]

        # make request
        url = f"/{self.test_addrs[0]}/tags/{tag_id}/votes/"
        data = [{"value": False}, {"value": True}]
        response = self.client.post(url, data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_vote_owner(self):
        """
        Assert that the creator of a Vote can update it.
        """
        # set up test
        # create nametag, note that an upvote is automatically
        # created by the user that created a nametag
        response = self.client.post(
            f"/{self.test_addrs[0]}/tags/",
            {"nametag": "Test Address One"}
        )
        tag_id = response.data["id"]
        vote = Vote.objects.get(tag=tag_id)

        # make request
        # change the upvote to a downvote
        url = f"/{self.test_addrs[0]}/votes/{vote.id}/"
        data = {"value": False}
        response = self.client.put(url, data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert that there is only 1 vote in the system
        votes = Vote.objects.all()
        self.assertEqual(len(votes), 1)

        # assert that the existing vote was updated to a downvote
        self.assertEqual(votes[0].value, False)

    def test_update_vote_not_owner(self):
        """
        Assert that a user cannot change someone else's vote,
        and that a 403 FORBIDDEN is returned.
        """
        # set up test
        # create nametag, note that an upvote is automatically
        # created by the user that created a nametag
        response = self.client.post(
            f"/{self.test_addrs[0]}/tags/",
            {"nametag": "Test Address One"}
        )
        tag_id = response.data["id"]
        vote = Vote.objects.get(tag=tag_id)

        # make request
        # try to update the vote as another user
        self.client.cookies.clear()  # no cookies means no session
        url = f"/{self.test_addrs[0]}/votes/{vote.id}/"
        data = {"value": False}
        response = self.client.put(url, data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Vote.objects.get(id=vote.id).value, True)

    def test_delete_vote_owner(self):
        """
        Assert that the creator of a Vote can delete it.
        """
        # set up test
        # create nametag, note that an upvote is automatically
        # created by the user that created a nametag
        response = self.client.post(
            f"/{self.test_addrs[0]}/tags/",
            {"nametag": "Test Address One"}
        )
        tag_id = response.data["id"]
        vote = Vote.objects.get(tag=tag_id)

        # make request
        # delete the vote
        url = f"/{self.test_addrs[0]}/votes/{vote.id}/"
        response = self.client.delete(url)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # assert that the vote no longer exists
        votes = Vote.objects.filter(id=vote.id)
        self.assertEqual(len(votes), 0)

    def test_delete_vote_not_owner(self):
        """
        Assert that a user cannot delete someone else's vote,
        and that a 403 FORBIDDEN is returned.
        """
        # set up test
        # create nametag, note that an upvote is automatically
        # created by the user that created a nametag
        response = self.client.post(
            f"/{self.test_addrs[0]}/tags/",
            {"nametag": "Test Address One"}
        )
        tag_id = response.data["id"]
        vote = Vote.objects.get(tag=tag_id)

        # make request
        # try to delete the vote as another user
        self.client.cookies.clear()  # no cookies means no session
        url = f"/{self.test_addrs[0]}/votes/{vote.id}/"
        response = self.client.delete(url)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(Vote.objects.filter(id=vote.id)), 1)

    def test_list_votes_nametag(self):
        """
        Assert that all votes for a specific nametag are returned.
        """
        # set up test
        # create nametag
        response = self.client.post(
            f"/{self.test_addrs[0]}/tags/",
            {"nametag": "Test Address One"}
        )
        tag_id = response.data["id"]

        # create two upvotes in addition to the
        # upvote that happens automatically on nametag creation
        url = f"/{self.test_addrs[0]}/tags/{tag_id}/votes/"
        data = {"value": True}
        self.client.post(url, data)
        self.client.post(url, data)

        # make request
        response = self.client.get(url)  # list votes for nametag

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]["value"], True)
        self.assertEqual(response.data[1]["value"], True)
        self.assertEqual(response.data[2]["value"], True)
