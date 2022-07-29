# backend

## Requirements  
* Python 3.8.10
* pg_config which is needed to install psycopg2 requirement. You can install it by running `sudo apt-get install libpq-dev` (on Ubuntu)  

## Installation
1. Clone the repo  
2. Run the build script: `./build.sh`

## Running Server
1. `source .env/bin/activate` 
2. `cd tagmi`  
3. `python manage.py runserver`  

## Running Tests
1. `source .env/bin/activate` 
2. `cd tagmi`  
3. `python manage.py test`  

## API Schema

Notes:
 * Client should support persistent cookies. The backend sets a cookie with a session id after a user creates a nametag or vote. This is then used by the backend to determine whether a user can edit a vote, etc.  

```
GET     /{address}/tags/
    Returns all nametags and their votes for a given address, sorted by decreasing net upvotes.

    Request Body
        {}

    Response Status
        200 if successful
        404 if address not found

    Response Body
        [
            {
                "id": 2,
                "nametag": "Address One Nametag Two",
                "votes": {
                    "upvotes": 2,
                    "downvotes": 0,
                    "userVoted": true,
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
                    "userVoted": true
                    "userVoteChoice": false
                },
                "createdByUser": false
            },
            {
                "id": 4,
                "nametag": "Address One Nametag Four",
                "votes": {
                    "upvotes": 2,
                    "downvotes": 1,
                    "userVoted": false
                    "userVoteChoice": null
                },
                "createdByUser": false
            },
            {
                "id": 1,
                "nametag": "Address One Nametag One",
                "votes": {
                    "upvotes": 1,
                    "downvotes": 1,
                    "userVoted": true
                    "userVoteChoice": null
                },
                "createdByUser": false
            }
        ]


POST    /{address}/tags/
    Creates a new nametag for a given address and auto-upvotes it.
    
    Request Body  
        {
            "nametag": "Test Address One"
        }

    Response Status
        201 if successful
        400 if bad address or nametag

    Response Body  
        {
            "id": 1,
            "nametag": "Test Address One",
            "votes": {
                "upvotes": 1,
                "downvotes": 0,
                "userVoted": true,
                "userVoteChoice": true
            },
        }


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
            "userVoted": true|false,
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
            "userVoted": true,
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
            "userVoted": true,
            "userVoteChoice": false
        }
```


## Notes
Never use the `sample-dev-env` file in production.  
In production, make sure to set the environment variables on the command line, or create a .env file with the appropriate values before running the `build.sh` script.  

`manage.py` has been edited to make tests use the settings module `./tagmi/test_settings.py`.  

When inserting validation logic in models, you must override the model's `save` method and call `self.full_clean` in it.  
Put all validation logic inside the model's `clean` method, and put all unique constraint validation inside the model's `validate_unique` method.  
I found that's the best way to enforce validation logic for API users going through the views/serializers, as well as developers interacting with the code directly.  

Do not do bulk updates with a queryset, i.e. Queryset.update unless you really know what you're doing.  
Meaning, you understand that the bulk update skips the model's `save` method completely and does not do any validation. So if you do it, you better be bulk updating with the correct values that obey all validation logic.  

At the moment we're creating a session for a user when they create a new nametag or vote. In the future as the code grows, we may want to move to a custom middleware that creates a session on each request as it comes in if the session does not already exist. This comes at the cost of writing to the database on each request if session does not exist.


## Future Feature Considerations
 * Pagination for nametags


## TODO
 * Lock down the configuration before deploying to production. Search for # TODO comments in the code, as well as going through this https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/
