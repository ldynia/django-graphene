import graphene
import graphene_django_optimizer as gql_optimizer

from django.db import connection
from graphene_django import DjangoObjectType

from demo.models import City
from demo.models import Continent
from demo.models import Country
from demo.models import District
from demo.models import Governor
from demo.models import Mayor
from demo.models import State

# from demo.gql.query_optimizer import GQOptimizer
# from demo.gql.query_optimizer_v2 import GQOptimizer
# from demo.gql.query_optimizer_martin import optimizer as GQOptimizer
from demo.gql.query_optimizer_v3 import optimizer


class ContinentType(DjangoObjectType):

    class Meta:
        model = Continent


class CountryType(DjangoObjectType):

    class Meta:
        model = Country


class StateType(DjangoObjectType):

    class Meta:
        model = State


class DistrictType(DjangoObjectType):

    class Meta:
        model = District


class MayorType(DjangoObjectType):

    class Meta:
        model = Mayor


class CityType(DjangoObjectType):

    class Meta:
        model = City


class GovernorType(DjangoObjectType):

    class Meta:
        model = Governor


import cProfile, pstats
from silk.profiling.profiler import silk_profile


class CountryQuery(graphene.ObjectType):

    all_cities = graphene.List(CityType)

    def resolve_all_cities(self, info):
        # profiler = cProfile.Profile()
        # profiler.enable()
        qs = optimizer(City.objects.all(), info)
        # profiler.disable()
        # stats = pstats.Stats(profiler)
        # stats.print_stats()
        return qs
        # return GQOptimizer(info).optimize(City.objects.all(), ['allCities'])
        # return gql_optimizer.query(City.objects.all(), info)


def test_time(self):
    payload = """"""
    profiler = cProfile.Profile()
    profiler.enable()
    self.query(payload)
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.print_stats()
