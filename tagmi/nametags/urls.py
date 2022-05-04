"""
URL router for nametags application.
"""
# std lib imports

# third party imports
from django.urls import path

# our imports
from .views import TagList


urlpatterns = [
    path('<str:address>/tags/', TagList.as_view()),
]
