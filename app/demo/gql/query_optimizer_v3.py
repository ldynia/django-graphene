from collections import Counter

from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related import ManyToManyField
from django.db.models.fields.reverse_related import ManyToManyRel
from django.db.models.fields.reverse_related import ManyToOneRel
from django.db.models.fields.reverse_related import OneToOneRel
from django.db.models.query import QuerySet

from graphql.language.ast import FieldNode
from graphql.type.definition import GraphQLResolveInfo


"""
query AllCities {
  allCities {
    state {
      governor {
        name
      }
      country {
        name
      }
    }
  }
}
"""
"""
query AllCities {
  allCities {
    district {
      city {
        mayor {
          city {
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
query AllCities {
  allCities {
    id
    name
    state {
      name
      governor {
        name
      }
      country {
        name
      }
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


def optimizer(qs: QuerySet, info: GraphQLResolveInfo, top_node: FieldNode=None):
    """
    This function optimizes queryset base on model relations extracted from graphql query.

    :param QuerySet qs: QuerySet of a model to be optimized.
    :param GraphQLResolveInfo info: GraphQL info context.
    :param FieldNode qs: Filed Node to be iterated

    :return: QuerySet:
    """
    model_relations = {
        'select_related': [],
        'prefetch_related': []
    }

    # Set top_node to the very first filed node found in graphql query.
    if not top_node:
        top_node = info.field_nodes[0]

    prefix_nodes = []
    for field_node in top_node.selection_set.selections:
        field_name = field_node.name.value
        # Check if filed exists on model.
        if hasattr(qs.model, field_name):
            models_field = qs.model._meta.get_field(field_name)
            # Check if field has nested models.
            if field_node.selection_set:
                # Check if field is in select related relationship.
                if isinstance(models_field, (ForeignKey, OneToOneRel)):
                    model_relations['select_related'].append(field_name)

                # Check if field is in prefetch related relationship.
                if isinstance(models_field, (ManyToManyField, ManyToManyRel, ManyToOneRel)):
                    model_relations['prefetch_related'].append(field_name)

                # Prefix map
                prefix_nodes.append((field_name, field_node))

    # Extract and normalize paths representing relations betwean models.
    paths = extract_path(prefix_nodes)
    paths = normalize_paths(paths)

    # Extract select_related and prefetch_related paths.
    select_related, prefetch_related = get_related(paths, model_relations)

    # Print related fields if they exist.
    if select_related or prefetch_related:
        print('select_related', select_related)
        print('prefetch_related', prefetch_related)

    # Catch generic exception if execution of optimized query failed. Otherwise run unmodified query.
    try:
        return qs.select_related(*select_related).prefetch_related(*prefetch_related)
    except Exception as err:
        print(f'Error: Query optimizer failed due to: {err} error.')
        print('Warning: Executing not optimized query instead. This might affect query performance.')
        return qs


def extract_path(nodes=[], paths=set()) -> set:
    """
    Function recursively extracts paths representing model relations extracted from graphql query.

    :param list nodes: List of FieldNodes. FieldNode is representing model to be extracted.
    :param set paths: Paths is a set used to construct prefixes for model relation.

    :return: set: Return set of strings containing paths of relations between models.
    """
    # Normalize default paramters and solve problem explained in below link.
    # link: https://florimond.dev/en/posts/2018/08/python-mutable-defaults-are-the-source-of-all-evil/
    nodes = nodes if nodes else []
    paths = paths if paths else set()

    # sub_prefix is a temporary list to hold prefixes extracted from currently iterated node.
    sub_prefix = []
    for node in nodes:
        prefix, field_node = node
        # Check if field node exist and has nested models.
        if field_node and field_node.selection_set:
            for sub_node in field_node.selection_set.selections:
                if sub_node.selection_set:
                    # Normalize prefix for fields that hold more than one model.
                    prefix = prefix + '__' + sub_node.name.value
                    if len(field_node.selection_set.selections) > 1:
                        prefix = field_node.name.value + '__' + sub_node.name.value

                    sub_prefix.append([prefix, sub_node])
                else:
                    sub_prefix.append([prefix, None])
        # Field node doesn't have nested models.
        else:
            paths.add(prefix)

    # Make recursive call only if there is data.
    if sub_prefix:
        return extract_path(sub_prefix, paths)

    return paths


def get_related(relations: list, relation_prefixes: dict) -> tuple:
    """
    Function extracts select_related and prefetch_related paths from model prefix.
    A model prefix is the field name extracted from top_node FileNode.

    :param list relations: Relations extracted from graphql query
    :param dict relation_prefixes: Dict that holds names of prefetch_related and select_related fields.

    :return: tuple: Returns a set of related fields. First element in tuple is select_related fields.
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
    Function normalizes paths extracted from graphql query.

    :param list paths: List of paths to be normalized.

    :return: list: List of normalized paths.
    """
    normalized_paths = []

    for path in set(paths):
        models = path.split('__')
        if len(models) == 1:
            normalized_paths.append(path)
        else:
            models_count = dict(Counter(models))
            for model, count in models_count.items():
                # If model appearsse more than 2 times in a path then remove duplicated model from it.
                if count >= 2:
                    path = model.join(path.split(model, 2)[:2])
                    path = path.strip('_')
            normalized_paths.append(path)

    return normalized_paths
