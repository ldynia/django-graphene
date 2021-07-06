import requests
import json

from django.core.management.base import BaseCommand

from demo.models import Movie
from demo.models import Actor
from demo.models import Country
from demo.models import State
from demo.models import City


class Command(BaseCommand):

    help = 'Seed database'

    def handle(self, *args, **options):
        self.__seed_locations()
        self.__seed_moives()

    def __seed_locations(self):
        print('Start saving locations.')

        with open('/app/demo/management/commands/data/locations.json') as file:
            locations = json.loads(file.read())
            for location in locations:
                country, created = Country.objects.get_or_create(name=location['country'])
                state, created = State.objects.get_or_create(name=location['state'], country=country)
                city, created = City.objects.get_or_create(name=location['city'], state=state)

        print('Done saving locations.')

    def __seed_moives(self):
        print('Start saving movies.')

        with open('/app/demo/management/commands/data/movies.json') as file:
            movies = json.loads(file.read())
            for movie in movies:
                print(movie['rank'], movie['title'])
                url = f"http://omdbapi.com/?apikey=b1da61a5&t={movie['title']}"
                r = requests.get(url)
                for star in r.json()['Actors'].split(", "):
                    try:
                        first_name, *_, last_name = star.split(' ')
                        actor, created = Actor.objects.get_or_create(
                            first_name=first_name,
                            last_name=last_name,
                        )
                    except ValueError as err:
                        actor, created = Actor.objects.get_or_create(
                            nick_name=star if star else None,
                        )

                    movie, created = Movie.objects.get_or_create(
                        title=r.json()['Title'],
                        rating=float(r.json()['imdbRating']) if r.json()['imdbRating'] != 'N/A' else 0,
                        year=int(r.json()['Year']),
                        genre=r.json()['Genre'].split(', '),
                    )

                    movie.actors.add(actor)

        print('Done saving movies.')
