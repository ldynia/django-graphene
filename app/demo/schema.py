import graphene
import graphene_django_optimizer as gql_optimizer

from graphene_django import DjangoObjectType

from demo.models import City
from demo.models import Continent
from demo.models import Country
from demo.models import District
from demo.models import Governor
from demo.models import Mayor
from demo.models import State

from django_gql_optimizer.optimizer import optimizer


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


class CountryQuery(graphene.ObjectType):

    all_cities = graphene.List(CityType)

    def resolve_all_cities(self, info):
        return optimizer(City.objects.all(), info.field_nodes[0])
        # return gql_optimizer.query(City.objects.all(), info)
