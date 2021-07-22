import graphene
import graphene_django_optimizer as gql_optimizer

from django.db import connection
from graphene_django import DjangoObjectType

from demo.models import City
from demo.models import Continent
from demo.models import Country
from demo.models import District
from demo.models import Mayor
from demo.models import State
# from demo.gql.query_optimizer import GQOptimizer
from demo.gql.query_optimizer_v2 import GQOptimizer


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


class CountryQuery(graphene.ObjectType):

    all_cities = graphene.List(CityType)

    def resolve_all_cities(self, info):
        return GQOptimizer(info).optimize(City.objects.all()[:10], ['allCities'])
        # return gql_optimizer.query(City.objects.all()[:10], info)
