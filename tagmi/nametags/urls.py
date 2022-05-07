"""
URL router for nametags application.
"""
# std lib imports

# third party imports
from django.urls import path

# our imports
from .views import TagList, VoteList


urlpatterns = [
    path('<str:address>/tags/', TagList.as_view()),
    path('<str:address>/tags/<int:tag_id>/votes/', VoteList.as_view()),
]
