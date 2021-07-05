from graphene_django import DjangoObjectType
import graphene


class User(DjangoObjectType):

    class Meta:
        model = UserModel


class Query(graphene.ObjectType):
    users = graphene.List(User)

    def resolve_users(self, info):
        return UserModel.objects.all()
