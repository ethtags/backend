"""
Module containing utility functions for the nametags application.
"""
# std lib imports

# third party imports
from django.db.models import Case, IntegerField, Sum, When

# our imports


def create_session_if_dne(request):
    """
    Creates a Session, saves it to the database,
    and attaches it to the given request,
    if it does not already exist on the given request.
    """
    # create session if it does not exist
    if request.session.session_key is None:
        request.session.save(must_create=True)


def order_nametags_queryset(queryset):
    """
    Returns a queryset that is ordered by
    descending net upvote count, and then by
    created datetime.
    """
    # annotate the tags so that they can be sorted by net upvote count
    # https://docs.djangoproject.com/en/4.0/topics/db/aggregation/
    # https://docs.djangoproject.com/en/4.0/ref/models/conditional-expressions/
    queryset = queryset.annotate(
        net_upvotes=Sum(
            Case(
                When(votes__value=True, then=1),
                When(votes__value=False, then=-1),
                When(votes__value=None, then=0),
                output_field=IntegerField()
            )
        )
    )

    # sort the queryset by descending net upvote count
    # (upvotes minus downvotes) from greatest to least
    queryset = queryset.order_by("-net_upvotes", "-created")

    return queryset
