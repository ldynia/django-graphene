from collections import Counter

from graphql.language.ast import FieldNode
from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related import ManyToManyField
from django.db.models.fields.reverse_related import ManyToManyRel
from django.db.models.fields.reverse_related import ManyToOneRel
from django.db.models.fields.reverse_related import OneToOneRel

"""
query AllCities {
  allCities {
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
"""

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
      city {
        id
        name
      }
    }
    district {
      name
      city {
        name
        mayor {
          lastName
          city {
            name
            district {
              name
            }
          }
        }
      }
    }
  }
}
"""

def optimizer(qs, info):
    relations = []
    relations_prefixes = {
        'select_related': [],
        'prefetch_related': []
    }

    for field in info.field_nodes[0].selection_set.selections:
        field_name = field.name.value
        models_field = qs.model._meta.get_field(field_name)
        # Check if field has nested models
        if field.selection_set:
            # Check if field is in select related relationship
            if isinstance(models_field, (ForeignKey, ManyToManyField, OneToOneRel)):
                relations_prefixes['select_related'].append(field_name)

            # Check if field is in prefetch related relationship
            if isinstance(models_field, (ManyToOneRel, ManyToManyRel)):
                relations_prefixes['prefetch_related'].append(field_name)

            # Append prefix to relations
            prefix = extract_path(field, field_name)
            relations.append(prefix)

    # Normalize paths in relations
    relations = normalize_paths(relations)

    # Extract select_related and prefetch_related paths
    select_related, prefetch_related = get_related(relations, relations_prefixes)
    print('select_related', select_related)
    print('prefetch_related', prefetch_related)

    return qs.select_related(*select_related).prefetch_related(*prefetch_related)


def extract_path(field_node: FieldNode, prefix='') -> str:
    """
    Recursively extract model name from select related field.

    :param FieldNode field_node: Field node is representing model.
    :param str prefix: Prefix is used to construct model relation paths.

    :return: str: relations between models
    """
    if field_node.selection_set:
        for sub_node in field_node.selection_set.selections:
            if sub_node.selection_set:
                prefix = prefix + '__' + sub_node.name.value
                return extract_path(sub_node, prefix)
    return prefix


def get_related(relations: list, relation_prefixes: dict) -> tuple:
    """
    Match model relations base on the relation prefixes.
    A relation prefix is a field name extracted from fields specified in 1st Field Node.

    :param list relations: Relations extracted from graphql query
    :param dict relation_prefixes: This dict holds names of the fields,
    for prefetch_related and select_related models.

    :return: tuple: holds set of related fields. First element in tuple is select_related fields.
    Second element in tuple is prefetch_related fields.
    """
    select_related = set()
    prefetch_related = set()
    for relation in relations:
        for srp in relation_prefixes['select_related']:
            if relation.startswith(srp):
                select_related.add(relation)

        for prp in relation_prefixes['prefetch_related']:
            if relation not in select_related and relation.startswith(prp):
                prefetch_related.add(relation)

    return select_related, prefetch_related


def normalize_paths(paths: list) -> list:
    """
    Normalize paths extracted from graphql.

    :param list paths: List of paths to be normalized.

    :return: list: Normalized paths.
    """
    normalized_paths = []
    for path in paths:
        models = path.split('__')
        if len(models) == 1:
            normalized_paths.append(path)
        else:
            models_count = dict(Counter(models))
            for model, count in models_count.items():
                # Remove duplicated models from graphql path
                if count >= 2:
                    path = model.join(path.split(model, 2)[:2])
                    path = path.strip('_')
            normalized_paths.append(path)

    return normalized_paths
