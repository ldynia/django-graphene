import re
import json
from collections import defaultdict

from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related import ManyToManyField
from django.db.models.fields.reverse_related import ManyToManyRel
from django.db.models.fields.reverse_related import ManyToOneRel
from django.db.models.fields.reverse_related import OneToOneRel
from django.db.models.query import QuerySet

"""
query AllCities {
  allCities {
    id
    name
    state {
      name
    }
    mayor {
      firstName
      lastName
      city {
        id
        name
      }
    }
    district {
      name
      city {
        mayor {
          lastName
        }
      }
    }
  }
}
"""


class GQOptimizer():
    """
    Class optimizes QuerySet base on information extracted from graphql query.
    """

    def __init__(self, info):
        self.info = info
        self.gql_query = info.field_nodes[0].loc.source.body
        self.select_related = set()
        self.prefetch_related = set()

        print(self.gql_query)

        # Print types
        for k, v in self.info.schema.type_map.items():
            print('Types', k, v)

    def optimize(self, queryset: QuerySet) -> QuerySet:
        root = self.info.field_name
        paths = defaultdict(list)
        print('1 field_nodes[0]', type(self.info.field_nodes[0]))
        print('2 self.info.field_nodes[0].selections', type(self.info.field_nodes[0].selection_set))

        # 1st level iteration
        for idx, selection in enumerate(self.info.field_nodes[0].selection_set.selections):
            print(f'3 selection', idx, type(selection), selection.name.value, selection.kind)
            if self.__filed_type(selection.name.value):
                # Create metadata filed
                paths[0].append({
                    'index': idx,
                    'root': root,
                    'field_name': selection.name.value,
                    'selection': root + '__' + selection.name.value
                })

        # Has nested types 2nd level iteration
        if len(paths[0]):
            for meta_field in paths[0]:
                idx = meta_field['index']
                field = self.info.field_nodes[0].selection_set.selections[idx]
                print('Meta', idx, meta_field['field_name'])
                for idx, selection in enumerate(field.selection_set.selections):
                    if self.__filed_type(selection.name.value):
                        paths[1].append({
                            'index': idx,
                            'root': root,
                            'field_name': meta_field['field_name'],
                            'selection': meta_field['selection'] + '__' + selection.name.value
                        })
                        print(f'4 selection', idx, type(selection), selection.name.value, selection.kind)

        print('Paths', json.dumps(paths))
        return queryset

    def __filed_type(self, field_name):
        """Check if field name has its Type"""
        field_name = field_name[0].upper() + field_name[1:] + 'Type'
        return field_name in self.info.schema.type_map.keys()
