"""
URL router for nametags application.
"""
# std lib imports

# third party imports
from django.urls import path

# our imports
from .views import TagListCreate, VoteGetUpdateDelete, VoteListCreate


urlpatterns = [
    path('<str:address>/tags/', TagListCreate.as_view()),
    path('<str:address>/tags/<int:tag_id>/votes/', VoteListCreate.as_view()),
    path('<str:address>/votes/<int:vote_id>/', VoteGetUpdateDelete.as_view()),
]
