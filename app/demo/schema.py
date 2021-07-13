import graphene
import graphene_django_optimizer as gql_optimizer

from django.db import connection
from graphene_django import DjangoObjectType

from demo.models import City
from demo.models import Continent
from demo.models import Country
from demo.models import District
from demo.models import State
from demo.gql.query_optimizer import GQOptimizer


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


class CityType(DjangoObjectType):

    class Meta:
        model = City


class CountryQuery(graphene.ObjectType):

    all_cities = graphene.List(CityType)

    def resolve_all_cities(self, info):
        # return City.objects.all()[:50]
        # return City.objects.all().prefetch_related('state__country')
        # return City.objects.all().select_related('state__country')
        # return City.objects.all().select_related('state__country_continent')
        # return query_optimizer(City.objects.all()[:3], info)
        query = City.objects.all()[:3]
        return GQOptimizer(info).optimize(query)
        # return gql_optimizer.query(City.objects.all(), info)
