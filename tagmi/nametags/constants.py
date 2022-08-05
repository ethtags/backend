"""
Module containing constants for the nametags application.
"""
# std lib imports
import re

# third party imports

# our imports


ADDRESS_FORMAT = re.compile(r"^0x[0-9a-f]{40}$", re.IGNORECASE | re.ASCII)
NAMETAG_FORMAT = re.compile(r"^[\w\-\s\,\.']+$")
