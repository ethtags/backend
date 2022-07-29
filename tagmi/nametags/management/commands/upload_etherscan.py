"""
Script that reads a csv file of address,nametag
and writes it to ETHTags database.
"""
# std lib imports
import csv
import uuid

# third party imports
from django.core.management.base import BaseCommand

# our imports
from nametags.models import Address, Tag


class Command(BaseCommand):
    """ Class representing a django manage.py command. """

    help = "\
        Adds etherscan labels to the application. \
        Requires a positional argument 'input_file' to be the path to a \
        csv file that contains rows of 'address,nametag'. \
        "

    session_key = str(uuid.uuid4())

    def add_arguments(self, parser):
        parser.add_argument("--input", type=str)

    def handle(self, *args, **options):
        # read csv file from command line
        with open(options["input"], "r", encoding="utf-8") as fdesc:
            reader = csv.DictReader(fdesc)

            # go through records, add them to database
            for row in reader:
                self.stdout.write(f"Adding: {row['address']},{row['nametag']}")
                address, _ = Address.objects.get_or_create(
                    pubkey=row["address"]
                )

                try:
                    Tag.objects.get(
                        address=address,
                        nametag=row["nametag"]
                    )
                except Tag.DoesNotExist:
                    Tag.objects.create(
                        address=address,
                        nametag=row["nametag"],
                        created_by_session_id=self.session_key,
                        source="etherscan"
                    )
