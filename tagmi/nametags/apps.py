"""
Application config for nametags app.
"""
from django.apps import AppConfig


class NametagsConfig(AppConfig):
    """ Sets attributes of parent class. """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nametags'
