"""
Module containing utility functions for the nametags application.
"""


def create_session_if_dne(request):
    """
    Creates a Session, saves it to the database,
    and attaches it to the given request,
    if it does not already exist on the given request.
    """
    # create session if it does not exist
    if request.session.session_key is None:
        request.session.save(must_create=True)
