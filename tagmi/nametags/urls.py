"""
URL router for nametags application.
"""
# std lib imports

# third party imports
from django.urls import path

# our imports
from .views import TagListCreate, VoteCreateListUpdateDelete


urlpatterns = [
    path('<str:address>/tags/', TagListCreate.as_view()),
    path(
        '<str:address>/tags/<int:tag_id>/votes/',
        VoteCreateListUpdateDelete.as_view()
    ),
]
