"""
Module containing utilities for scraper jobs.
"""
# std lib imports
import logging
import uuid

# third party imports

# our imports
from ...models import Address, Tag


logger = logging.getLogger(__name__)


def add_label_to_db(label, source, address):
    """
    Adds the given label to the Tags database.
    Does nothing if the given label is None.
    Returns None.
    """
    if label is None:
        return

    # get or create address
    address_obj, _ = Address.objects.get_or_create(
        pubkey=address
    )

    # create Tag if it does not exist
    if not Tag.objects.filter(
        address=address_obj, nametag=label
    ).exists():
        logger.info("new label found, adding it to Tags table")
        Tag.objects.create(
            address=address_obj,
            nametag=label,
            created_by_session_id=str(uuid.uuid4()),
            source=source
        )
