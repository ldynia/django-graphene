import requests
import json
import names

from django.core.management.base import BaseCommand
from uuid import uuid4

from demo.models import Actor
from demo.models import City
from demo.models import Continent
from demo.models import Country
from demo.models import District
from demo.models import Movie
from demo.models import Mayor
from demo.models import State
from django.core.exceptions import FieldError
from django.core.exceptions import FieldError

class Command(BaseCommand):

    help = 'Catch Exceptions'

    def handle(self, *args, **options):
        try:
            print(City.objects.select_related('district'))
        except FieldError as err:
            print('Select Related Error:', err)

        try:
            print(City.objects.prefetch_related('mayorx'))
        except AttributeError as err:
            print('Prefetch Related Error:', err)
