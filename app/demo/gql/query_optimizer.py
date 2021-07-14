import re

from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related import ManyToManyField
from django.db.models.fields.reverse_related import ManyToManyRel
from django.db.models.fields.reverse_related import ManyToOneRel
from django.db.models.fields.reverse_related import OneToOneRel
from django.db.models.query import QuerySet


class GQOptimizer():
    """
    Class optimizes QuerySet base on information extracted from graphql query.
    """

    def __init__(self, info):
        self.info = info
        self.gql_query = info.field_nodes[0].loc.source.body
        self.select_related = ''
        self.prefetch_related = set()
        # print(self.gql_query)

    def optimize(self, queryset: QuerySet) -> QuerySet:
        """
        Method optimizes QuerySet base on extracted fields from graphql query.
        Once fields are relations, it will figure out if the field has forward or reverse
        relationship between related models. It is important to distinguish differences
        between model relationships because if relationship is forward then queryset parameters
        should go to Model.objects.select_related('model1__model2__modelN') method.
        On the other side if relationship betwean models is reverse then it should go to
        Model.objects.select_related('field', 'field', 'field') method.

        :param queryset: QuerySet

        :return: QuerySet
        """
        gql_nested_query = self.gql_query.count('{') - 1 >= 2
        if gql_nested_query:
            for selection in self.info.field_nodes[0].selection_set.selections:
                field_name = selection.loc.start_token.value
                if not field_name.startswith('__'):
                    field = queryset.model._meta.get_field(field_name)
                    # Check if Field has reverse relation
                    if isinstance(field, (ManyToOneRel, ManyToManyRel, OneToOneRel)):
                        self.prefetch_related.add(field_name)
                        gql_query_node = self.gql_query[selection.loc.start:selection.loc.end]
                        self.select_related = self.__extract_related(gql_query_node)

                    # Check if Field has forward relation
                    if isinstance(field, (ForeignKey, ManyToManyField)):
                        gql_query_node = self.gql_query[selection.loc.start:selection.loc.end]
                        self.select_related = self.__extract_related(gql_query_node)

            # Normalize prefetch_related and select_related
            self.__normalizer(queryset)

            # Create query with prefetch related
            if self.prefetch_related:
                # print('PREFETCH RELATED', *self.prefetch_related)
                queryset = queryset.prefetch_related(*self.prefetch_related)

            # Create query with select related
            if self.select_related:
                # print('SELECT RELATED', self.select_related)
                queryset = queryset.select_related(self.select_related)

        return queryset

    def __normalizer(self, queryset: QuerySet) -> None:
        """
        Method performs various normalization steps on self.select_related and
        self.prefetch_related fields.

        :param queryset: QuerySet

        :return: None
        """
        for field_name in self.prefetch_related:
            # Remove reverse related fields from self.select_related
            self.select_related = self.select_related.replace(field_name, '').strip('_')

            # Remove model name for self.select_related
            model_name = queryset.model.__name__.lower()
            self.select_related = self.select_related.replace(model_name, '').strip('_')

            for field_name in self.select_related.split('__'):
                try:
                    field = queryset.model._meta.get_field(field_name)
                    if isinstance(field, (ManyToOneRel, ManyToManyRel, OneToOneRel)):
                        # Make user that prefetched field is in self.prefetch_related set
                        self.prefetch_related.add(field_name)
                        # Remove reversed fields form self.select_related string
                        self.select_related = self.select_related.replace(field_name, '').strip('_')
                except:
                    pass

    def __extract_related(self, gql_query: str) -> str:
        """
        The method uses regular expressions to extract a path of related models.
        Path is extracted from graphql query string.

        Example of input string representing graphql query.
        {
           allCities {
                name
                state {
                    name
                    country {
                        name
                        continent {
                            name
                        }
                    }
                }
            }
        }
        Output string generated from input string will look like this "state__country_continent".

        :param gql_query: string representing graphql query

        :return: string
        """

        related_model_str = ''
        RE_MATCH_MODEL = '^\w+'
        RE_MATCH_NESTED_MODELS = '^\w+.*{$\n'
        gql_query = gql_query.replace(' ', '')

        # Find all nested (related) models in query
        matches = re.finditer(RE_MATCH_NESTED_MODELS, gql_query, re.MULTILINE)
        for match in matches:
            # Extract field name
            match = re.search(RE_MATCH_MODEL, match.group())
            related_model_str += match.group() + '__'

        return related_model_str.strip('_')
