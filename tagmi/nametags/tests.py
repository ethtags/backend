"""
Module containing tests for the nametags application.
# TODO
  rename session_id to session_key
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
        # common test addresses
        self.test_addrs = [
            "0x4622BeF7d6C5f7f1ACC479B764688DC3E7316d68",
            "0x41329485877D12893bC4ef88A9208ee5cB5f5525"
        ]

        # common test urls
        self.urls = {}
        self.urls["create"] = f"/{self.test_addrs[0]}/tags/"
        self.urls["list"] = self.urls["create"]

        # common test request data
        self.tag_value = "Test Address One"
        self.req_data = {"nametag": self.tag_value, "recaptcha": "dummy"}
        self.vote_req_data = {"value": True, "recaptcha": "dummy"}

    def test_create_nametag(self):
        """
        Assert that a nametag is created for the given address.
        Assert that the response contains the newly created nametag.
        """
        # set up test
        # make request
        response = self.client.post(self.urls["create"], self.req_data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected = {
            "id": 1,
            "nametag": self.req_data["nametag"],
            "createdByUser": True,
            "votes": {
                "upvotes": 1,
                "downvotes": 0,
                "userVoted": True,
                "userVoteChoice": True
            }
        }
        self.assertDictEqual(response.data, expected)

    def test_create_nametag_address_dne(self):
        """
        Assert that a new address is created when it does not exist.
        Assert that a new nametag is created for the new address.
        Assert that an upvote is created for the new nametag.
        """
        # set up test
        # make request
        response = self.client.post(self.urls["create"], self.req_data)

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
            self.tag_value
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

    def test_create_nametag_address_exists(self):
        """
        Assert that a new nametag is created for an existing address.
        Assert that an upvote is created for the new nametag.
        """
        # set up test
        Address.objects.create(
            pubkey=self.test_addrs[0]
        )

        # assert that address count is 1
        self.assertEqual(Address.objects.count(), 1)

        # make request
        response = self.client.post(self.urls["create"], self.req_data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # no new address created, count should still be 1
        self.assertEqual(Address.objects.count(), 1)

        # Tag created
        self.assertEqual(Tag.objects.count(), 1)
        tag_one = Tag.objects.get(id=1)
        self.assertEqual(
            tag_one.nametag,
            self.tag_value
        )
        self.assertEqual(
            tag_one.address.pubkey,
            self.test_addrs[0].lower()
        )

        # Vote created
        self.assertEqual(Vote.objects.count(), 1)

    def test_create_nametag_exists(self):
        """
        Assert that a 400 BAD REQUEST is returned if a nametag
        with the same value already exists for a given address.
        """
        # set up test
        # create tag
        response = self.client.post(self.urls["create"], self.req_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # make request
        # create the same nametag for the same address
        response = self.client.post(self.urls["create"], self.req_data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # assert that no new Tag was created
        tags = Tag.objects.all()
        self.assertEqual(len(tags), 1)

    def test_create_nametag_exists_diff_address(self):
        """
        Assert that a new nametag is created for a given address even
        if a nametag with the same value already exists for a
        different address.
        """
        # set up test
        # create a nametag for address one
        response = self.client.post(self.urls["create"], self.req_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # make request
        # create a nametag for address two
        url = f"/{self.test_addrs[1]}/tags/"
        response = self.client.post(url, self.req_data)

        # make assertions
        # assert that the response was a 201 with the new tag created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["nametag"], self.tag_value)

        # assert that both addresses have a nametag with the same value
        self.assertTrue(
            Tag.objects.filter(
                address=self.test_addrs[0].lower(),
                nametag=self.tag_value
            ).exists()
        )
        self.assertTrue(
            Tag.objects.filter(
                address=self.test_addrs[1].lower(),
                nametag=self.tag_value
            ).exists()
        )

    def test_create_nametag_invalid_address(self):
        """
        Assert that a 400 BAD REQUEST is returned when a
        user creates a new address that is invalid.
        """
        # address without 0x prepended
        url = f"/{self.test_addrs[0][2:42]}/tags/"
        response = self.client.post(url, self.req_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # address with invalid hex after 0x
        # note there is an uppercase Z at the end of the address in the URL
        url = f"/{self.test_addrs[0][0:41]}Z/tags/"
        response = self.client.post(url, self.req_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # address that is too short
        url = f"/{self.test_addrs[0][0:41]}/tags/"
        response = self.client.post(url, self.req_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # address that is too long
        # note there is an extra A at the end of the address in the URL
        url = f"/{self.test_addrs[0]}A/tags/"
        response = self.client.post(url, self.req_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_nametags(self):
        """
        Assert that a list of all nametags related to an address are returned.
        """
        # set up test
        # create nametags for addresses one and two
        self.req_data["nametag"] = "Address One Nametag One"
        self.client.post(self.urls["create"], self.req_data)

        self.req_data["nametag"] = "Address One Nametag Two"
        self.client.post(self.urls["create"], self.req_data)

        url = f"/{self.test_addrs[1]}/tags/"
        self.req_data["nametag"] = "Address Two Nametag One"
        self.client.post(url, self.req_data)

        # make request
        # list nametags for address one
        response = self.client.get(self.urls["list"])

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
        self.req_data['nametag'] = "Address One Nametag One"
        self.client.post(self.urls["create"], self.req_data)
        self.req_data['nametag'] = "Address One Nametag Two"
        self.client.post(self.urls["create"], self.req_data)

        # make request
        response = self.client.get(self.urls["list"])

        # make assertions
        # assert that votes exist for each created tag
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # two tags
        self.assertEqual(
            response.data[0]["votes"]["upvotes"],
            1
        )
        self.assertEqual(
            response.data[1]["votes"]["upvotes"],
            1
        )
        self.assertEqual(
            response.data[1]["votes"]["userVoteChoice"],
            True
        )

    def test_list_nametags_created_by_user(self):
        """
        Assert that the "createdByUser" field on a nametag is
        True/False if the requesting user created that nametag.
        """
        # set up test
        # create nametags for addresses one and two
        self.req_data["nametag"] = "Nametag One"
        self.client.post(self.urls["create"], self.req_data)

        self.req_data["nametag"] = "Nametag Two"
        self.client.post(self.urls["create"], self.req_data)

        # list nametags as the user that created the nametags
        # and assert that createdByUser is True
        response = self.client.get(self.urls["list"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["createdByUser"], True)
        self.assertEqual(response.data[1]["createdByUser"], True)

        # list nametags as a new user that did not created the nametags
        # and assert that createdByUser is False
        self.client.cookies.clear()
        response = self.client.get(self.urls["list"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["createdByUser"], False)
        self.assertEqual(response.data[1]["createdByUser"], False)

    def test_list_nametags_sorted(self):
        """
        Assert that listing nametags returns them sorted
        from greatest to least net upvote count.
        """
        # set up test
        # create three nametags
        self.req_data["nametag"] = "Nametag One"
        one = self.client.post(self.urls["create"], self.req_data)
        self.req_data["nametag"] = "Nametag Two"
        two = self.client.post(self.urls["create"], self.req_data)
        self.req_data["nametag"] = "Nametag Three"
        three = self.client.post(self.urls["create"], self.req_data)

        # upvote Nametag Three 3 times
        # upvote Nametag Two 3 times and downvote once
        # upvote Nametag One 3 times and downvote twice
        self._vote_tag_n_times(self.test_addrs[0], three.data["id"], True, 3)
        self._vote_tag_n_times(self.test_addrs[0], two.data["id"], True, 3)
        self._vote_tag_n_times(self.test_addrs[0], two.data["id"], False, 1)
        self._vote_tag_n_times(self.test_addrs[0], one.data["id"], True, 3)
        self._vote_tag_n_times(self.test_addrs[0], one.data["id"], False, 2)

        # GET the nametags
        response = self.client.get(self.urls["list"])

        # assert that Nametag Three is first
        # assert that Nametag Two is second
        # assert that Nametag One is third
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["id"], 3)
        self.assertEqual(response.data[1]["id"], 2)
        self.assertEqual(response.data[2]["id"], 1)

    def _vote_tag_n_times(self, address, tag_id, vote_value, num):
        """
        Upvotes/Downvotes the given address/nametag num amount of times.
        vote_value should be True for upvote, False for downvote.
        """
        url = f"/{address}/tags/{tag_id}/votes/"
        for _ in range(num):
            self.client.cookies.clear()
            self.vote_req_data["value"] = vote_value
            resp = self.client.post(url, self.vote_req_data)
            assert resp.status_code == 201


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

        # common test request data
        self.req_data = {"value": True, "recaptcha": "dummy"}
        self.tag_req_data = {
            "nametag": "Test Address One",
            "recaptcha": "dummy"
        }

        # create nametag
        response = self.client.post(
            f"/{self.test_addrs[0]}/tags/",
            self.tag_req_data
        )
        self.tag_id = response.data["id"]
        self.vote_id = Vote.objects.get(tag=self.tag_id).id

        # common test urls
        self.urls = {}
        self.urls["list"] = f"/{self.test_addrs[0]}/tags/{self.tag_id}/votes/"
        self.urls["create"] = self.urls["list"]
        self.urls["update"] = self.urls["list"]

    def test_upvote_nametag(self):
        """
        Assert that an upvote is created for the desired nametag.
        """
        # make request
        self.client.cookies.clear()  # refresh cookies to act as a new user
        response = self.client.post(self.urls["create"], self.req_data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert the nametag now has two votes,
        # one from creation and a second from upvoting
        votes = Vote.objects.filter(tag=self.tag_id)
        self.assertEqual(len(votes), 2)

        # assert that both votes are upvotes
        self.assertEqual(votes[0].value, True)
        self.assertEqual(votes[1].value, True)

        # assert that the second vote was created by the new user
        self.assertEqual(
            votes[1].created_by_session_id,
            self.client.cookies.get("sessionid").value
        )

    def test_downvote_nametag(self):
        """
        Assert that a downvote is created for the desired nametag.
        """
        # make request
        self.req_data["value"] = False
        self.client.cookies.clear()  # refresh cookies to act as a new user
        response = self.client.post(self.urls["create"], self.req_data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # assert the nametag now has two votes,
        # one from Tag creation in setUp and a second from downvoting
        votes = Vote.objects.filter(tag=self.tag_id)
        self.assertEqual(len(votes), 2)
        self.assertEqual(votes[0].value, True)
        self.assertEqual(votes[1].value, False)

        # assert that the second vote was created by the new user
        self.assertEqual(
            votes[1].created_by_session_id,
            self.client.cookies.get("sessionid").value
        )

    def test_post_multiple_votes_nametag(self):
        """
        Assert that an attempt to create multiple votes
        for the same nametag by the same user is not allowed.
        """
        # make request
        # note cookies aren't cleared here so the request
        # is being sent by the same user as the setUp method
        response = self.client.post(self.urls["create"], self.req_data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_vote_owner(self):
        """
        Assert that the creator of a Vote can update it.
        """
        # make request
        # change the upvote to a downvote
        # note that the vote was created in the setUp method
        self.req_data["value"] = False
        response = self.client.put(self.urls["update"], self.req_data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # assert that there is only 1 vote in the system
        votes = Vote.objects.all()
        self.assertEqual(len(votes), 1)

        # assert that the existing vote was updated to a downvote
        self.assertEqual(votes[0].value, False)

    def test_update_vote_not_owner(self):
        """
        Assert that a user cannot update a vote if they haven't created one.
        Assert that a 404 NOT FOUND is returned.
        """
        # make request
        # try to update the vote created in the setUp method
        self.client.cookies.clear()  # refresh cookies to act as a new user
        self.req_data["value"] = False
        response = self.client.put(self.urls["update"], self.req_data)

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Vote.objects.get(id=self.vote_id).value, True)

    def test_list_votes_nametag(self):
        """
        Assert that all votes for a specific nametag are returned.
        """
        # set up test
        # create two upvotes in addition to the setUp method
        self.client.cookies.clear()  # refresh cookies to act as a new user
        self.client.post(self.urls["create"], self.req_data)
        self.client.cookies.clear()  # refresh cookies to act as a new user
        self.client.post(self.urls["create"], self.req_data)

        # make request
        response = self.client.get(self.urls["list"])  # list votes for nametag

        # make assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["upvotes"], 3)
        self.assertEqual(response.data["downvotes"], 0)

    def test_list_votes_vote_choice_field(self):
        """
        Assert that listing votes of a nametag returns a
        "userVoteChoice" field which is
            null if the requestor has voted on the nametag but undid it.
            true if the requestor upvoted the nametag.
            false if the requestor downvoted the nametag.
        """
        # set up test
        # note that cookies aren't cleared before this request, therefore
        # the user is the same as the one that created
        # the nametag and auto-upvote in the setUp method
        response = self.client.get(self.urls["list"])
        self.assertEqual(response.data["userVoteChoice"], True)

        # create a downvote as a new user and
        # assert that userVoteChoice is False
        self.client.cookies.clear()  # refresh cookies to act as a new user
        self.req_data["value"] = False
        self.client.post(self.urls["create"], self.req_data)
        response = self.client.get(self.urls["list"])
        self.assertEqual(response.data["userVoteChoice"], False)

        # list votes as a new user that has undone their vote and
        # assert that userVoteChoice is null
        self.req_data["value"] = None
        self.client.put(self.urls["update"], self.req_data)
        response = self.client.get(self.urls["list"])
        self.assertEqual(response.data["userVoteChoice"], None)

    def test_list_votes_user_voted_field(self):
        """
        Assert that listing votes of a nametag returns a
        "userVoted" field which is
            true if the requestor has voted or unvoted the nametag.
            false if the requestor has never voted on the nametag before.
        """
        # set up test
        # note that cookies aren't cleared before this request, therefore
        # the user is the same as the one that created
        # the nametag and auto-upvote in the setUp method
        # assert that userVoted is True
        response = self.client.get(self.urls["list"])
        self.assertEqual(response.data["userVoted"], True)

        # undo the vote and assert that userVoted is still True
        self.req_data["value"] = None
        self.client.post(self.urls["update"], self.req_data)
        response = self.client.get(self.urls["list"])
        self.assertEqual(response.data["userVoted"], True)

        # list the nametags as a new user and
        # assert that userVoted is False
        self.client.cookies.clear()  # refresh cookies to act as a new user
        response = self.client.get(self.urls["list"])
        self.assertEqual(response.data["userVoted"], False)
