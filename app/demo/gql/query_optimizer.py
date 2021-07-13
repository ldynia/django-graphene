import re

from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related import ManyToManyField
from django.db.models.fields.reverse_related import ManyToManyRel
from django.db.models.fields.reverse_related import ManyToOneRel



class GQOptimizer():

    def __init__(self, info):
        self.info = info
        self.gql_query = info.field_nodes[0].loc.source.body
        print(self.gql_query)

    def optimize(self, queryset):
        model_name = queryset.model.__name__
        queryset_info = {model_name : {}}

        for k, v in self.info.schema.type_map.items():
            print(k, v)

        gql_nested_query = self.gql_query.count('{') - 1 >= 2
        if gql_nested_query:
            select_related = ''
            for selection in self.info.field_nodes[0].selection_set.selections:
                field_name = selection.loc.start_token.value
                # Check if FieldNode has forward relation
                field = queryset.model._meta.get_field(field_name)
                if isinstance(field, (ForeignKey, ManyToOneRel, ManyToManyRel, ManyToManyField)):
                    field_type = self.__field_name_to_type(field_name)
                    has_type = self.__has_type(field_type)
                    if has_type:
                        field_depth = self.__get_leaf_depth(selection)
                        gql_query_node = self.gql_query[selection.loc.start:selection.loc.end]
                        select_related = self.__match_selected(gql_query_node)
                        print('AAA', field_name, field_depth, select_related)
                        self.__validate_relations(field, select_related)

            if select_related:
                print('SELECT_RELATED', select_related)
                queryset = queryset.select_related(select_related)

        return queryset


    def __validate_relations(self, field, select_related):
        models = []
        separator  = '__'
        if separator in select_related:
            models = select_related.split(separator)[1:]

        if len(models) == 2:
            try:
                field.related_model._meta.get_field(models[0]) \
                    .related_model._meta.get_field(models[1])
            except FieldDoesNotExist as err:
                raise Exception(f'Optimizer Error: {err}')

        if len(models) == 3:
            try:
                field.related_model._meta.get_field(models[0]) \
                    .related_model._meta.get_field(models[1]) \
                    .related_model._meta.get_field(models[2])
            except FieldDoesNotExist as err:
                raise Exception(f'Optimizer Error: {err}')

        if len(models) == 4:
            try:
                field.related_model._meta.get_field(models[0]) \
                    .related_model._meta.get_field(models[1]) \
                    .related_model._meta.get_field(models[2]) \
                    .related_model._meta.get_field(models[3])
            except FieldDoesNotExist as err:
                raise Exception(f'Optimizer Error: {err}')

        if len(models) == 5:
            try:
                field.related_model._meta.get_field(models[0]) \
                    .related_model._meta.get_field(models[1]) \
                    .related_model._meta.get_field(models[2]) \
                    .related_model._meta.get_field(models[3]) \
                    .related_model._meta.get_field(models[4])
            except FieldDoesNotExist as err:
                raise Exception(f'Optimizer Error: {err}')

    def __get_leaf_depth(self, field_node):
        gql_query_node = self.gql_query[field_node.loc.start:field_node.loc.end]
        print(gql_query_node)
        return gql_query_node.count('{')

    def __get_type(self, name):
        return self.info.schema.type_map[name]

    def __match_selected(self, gql_query):
        model_related_str = ""
        re_match_model = '^\w+'
        re_match_nested_models = '^\w+.*{$\n'

        gql_query = gql_query.replace(' ', '')
        matches = re.finditer(re_match_nested_models, gql_query, re.MULTILINE)
        for match in matches:
            match = re.search(re_match_model, match.group())
            model_related_str += match.group() + '__'

        return model_related_str.strip('__')


    def __has_type(self, name):
        return name in self.info.schema.type_map.keys()


    def __field_name_to_type(self, name):
        stop_words = ('Set',)
        for word in stop_words:
            if name.endswith(word):
                name = name.replace(word, '')

        return name[0].upper() + name[1:] + 'Type'
