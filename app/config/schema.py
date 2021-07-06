import graphene

from demo.schema import CountryQuery


class Query(CountryQuery, graphene.ObjectType):
    pass


class Mutation(graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query)