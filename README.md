# backend

## Installation
1. Clone the repo  
2. Run the build script: `./build.sh`

## Running
1. `source .env/bin/activate` 
2. `cd tagmi`  
3. `python manage.py runserver`  

## API Schema

Notes:
 * Client should support persistent cookies. The backend sets a cookie with a session id after a user creates a nametag or vote. This is then used by the backend to determine whether a user can edit a vote, delete a vote, etc.  

```
GET     /{address}/tags/
    Returns all nametags and their votes for a given address, sorted by decreasing net upvotes.

    Request Body
        {}

    Response Status
        200 if success
        404 if address not found

    Response Body
        [
            {
                "id": 2,
                "nametag": "Address One Nametag Two",
                "votes": {
                    "upvotes": 2,
                    "downvotes": 0,
                    "userVoteChoice": true
                },
                "createdByUser": true
            },
            {
                "id": 3,
                "nametag": "Address One Nametag Three",
                "votes": {
                    "upvotes": 2,
                    "downvotes": 1,
                    "userVoteChoice": false
                },
                "createdByUser": false
            },
            {
                "id": 1,
                "nametag": "Address One Nametag One",
                "votes": {
                    "upvotes": 1,
                    "downvotes": 1,
                    "userVoteChoice": null
                },
                "createdByUser": false
            }
        ]
    

GET     /{address}/tags/{tag_id}/votes/
    Returns the count of all votes for a given address and nametag.

    Request Body
        {}

    Response Status
        200 if success
        404 if tag_id not found

    Response Body
        {
            "upvotes": 0,
            "downvotes": 0,
            "userVoteChoice": true|false|null
        }


POST    /{address}/tags/{tag_id}/votes/
    Upvote/Downvote a given address and nametag

    Request Body
        {
            "value": true
        }

    Response Status
        201 if successful
        400 if invalid request data or if user vote already exists
        404 if tag_id not found

    Response Body
        {
            "upvotes": 2,
            "downvotes": 0,
            "userVoteChoice": true
        }


PUT     /{address}/tags/{tag_id}/votes/
    Update a vote for a given address and nametag, must have been created by the requestor. If the requestor clears cookies (changes sessionid) then they will not be able to update their previous vote.
    Request Body
        {
            "value": false
        }

    Response Status
        200 if successful
        400 if invalid request data
        404 if tag_id not found

    Response Body
        {
            "upvotes": 1,
            "downvotes": 1,
            "userVoteChoice": false
        }


DELETE  /{address}/tags/{tag_id}/votes/
    Delete a vote for a given address and nametag, must have been created by the requestor. If the requestor clears cookies (changes sessionid) then they will not be able to delete their previous vote.

    Request Body
        {}

    Response Status
        200 if successful
        400 if invalid request data
        404 if tag_id not found

    Response Body
        {
            "upvotes": 1,
            "downvotes": 0,
            "userVoteChoice": null
        }
```


## Notes
Never use the `dev.env` file in production.  
In production, make sure to set the environment variables on the command line, or create a .env file with the appropriate values before running the `build.sh` script.  

When inserting validation logic in models, you must override the model's `save` method and call `self.full_clean` in it.  
Put all validation logic inside the model's `clean` method, and put all unique constraint validation inside the model's `validate_unique` method.  
I found that's the best way to enforce validation logic for API users going through the views/serializers, as well as developers interacting with the code directly.  

Do not do bulk updates with a queryset, i.e. Queryset.update unless you really know what you're doing.  
Meaning, you understand that the bulk update skips the model's `save` method completely and does not do any validation. So if you do it, you better be bulk updating with the correct values that obey all validation logic.  

At the moment we're creating a session for a user when they create a new nametag or vote. In the future as the code grows, we may want to move to a custom middleware that creates a session on each request as it comes in if the session does not already exist. This comes at the cost of writing to the database on each request if session does not exist.


## Future Feature Considerations
 * Pagination for nametags
 * Recaptcha with https://github.com/llybin/drf-recaptcha 
