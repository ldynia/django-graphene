from collections import Counter

from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related import ManyToManyField
from django.db.models.fields.reverse_related import ManyToManyRel
from django.db.models.fields.reverse_related import ManyToOneRel
from django.db.models.fields.reverse_related import OneToOneRel


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
"""
query {
  allLibrary {
    results {
      book {
        authors {
          fullName
        }
        owner {
          firstName
        }
      }
    }
  }
}
"""

def optimizer(qs, info, top_node=None):
    relations = []
    relations_prefixes = {
        'select_related': [],
        'prefetch_related': []
    }

    if not top_node:
        top_node = info.field_nodes[0]

    prefixes = []
    for field_node in top_node.selection_set.selections:
        field_name = field_node.name.value
        # Check if filed exists on model
        if hasattr(qs.model, field_name):
            models_field = qs.model._meta.get_field(field_name)
            # Check if field has nested models
            if field_node.selection_set:
                # Check if field is in select related relationship
                if isinstance(models_field, (ForeignKey, ManyToManyField, OneToOneRel)):
                    relations_prefixes['select_related'].append(field_name)

                # Check if field is in prefetch related relationship
                if isinstance(models_field, (ManyToOneRel, ManyToManyRel)):
                    relations_prefixes['prefetch_related'].append(field_name)

                # Prefix map
                prefixes.append((field_name, field_node))

    # Append prefix to relations
    relations = extract_path(prefixes)

    print('Before Normalization', relations)
    # Normalize paths in relations
    relations = normalize_paths(relations)
    print('After Normalization', relations)

    # Extract select_related and prefetch_related paths
    select_related, prefetch_related = get_related(relations, relations_prefixes)
    print('select_related', select_related)
    print('prefetch_related', prefetch_related)

    return qs.select_related(*select_related).prefetch_related(*prefetch_related)[:10]


def extract_path(prefixes=[], res=set()) -> str:
    """
    Recursively extract model name from from graphql query.

    :param FieldNode field_node: Field node is representing model.
    :param str prefix: Prefix is used to construct model relation paths.

    :return: str: relations between models
    """
    sub_prefix = []
    for prx in prefixes:
        path, field_node = prx
        # Field node has nested models
        if field_node and field_node.selection_set:
            for sub_node in field_node.selection_set.selections:
                if sub_node.selection_set:
                    path = path + '__' + sub_node.name.value
                    sub_prefix.append([path, sub_node])
                else:
                    sub_prefix.append([path, None])
        # Field node doesn't have nested models
        else:
            res.add(path)

    # Make recursive call only if there is a data
    if sub_prefix:
        res = remove_duplicates(sub_prefix, res)
        return extract_path(sub_prefix, res)

    return res

    # prefix_subnode = []
    # if field_node.selection_set:
    #     for sub_node in field_node.selection_set.selections:
    #         if sub_node.selection_set:
    #             lp = field_node.name.value + '__' + sub_node.name.value
    #             for prx in prefix:
    #                 local_prefixes.append(prx + '__' + sub_node.name.value)
    #     return extract_path(sub_node, prefix)
    # return prefix


def remove_duplicates(data: list, results: set) -> set:
    for item in data:
        results.discard(item[0])
    return results


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
        # Construct select related fields.
        for srp in relation_prefixes['select_related']:
            if relation.startswith(srp):
                select_related.add(relation)

        # Construct prefetch related fields.
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

    for path in set(paths):
        models = path.split('__')
        if len(models) == 1:
            normalized_paths.append(path)
        else:
            models_count = dict(Counter(models))
            for model, count in models_count.items():
                # Remove duplicated models from graphql path.
                if count >= 2:
                    path = model.join(path.split(model, 2)[:2])
                    path = path.strip('_')
            normalized_paths.append(path)

    return normalized_paths
