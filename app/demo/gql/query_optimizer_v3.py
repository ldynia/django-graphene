from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related import ManyToManyField
from django.db.models.fields.reverse_related import ManyToManyRel
from django.db.models.fields.reverse_related import ManyToOneRel
from django.db.models.fields.reverse_related import OneToOneRel
from django.db.models.query import QuerySet

from graphql.language.ast import FieldNode


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
    state {
      name
    }
    mayor {
      city {
        name
      }
    }
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


def optimizer(qs: QuerySet, top_node: FieldNode):
    """
    Function optimizes queryset base on model relations extracted from graphql query.

    :param QuerySet qs: QuerySet of a model to be optimized.
    :param FieldNode qs: Filed Node to be iterated.

    :return: QuerySet:
    """
    prefix_nodes = []
    model_relations = {
        'select_related': [],
        'prefetch_related': []
    }

    # Loop over every element (FileNode) in top_node.
    for field_node in top_node.selection_set.selections:
        field_name = field_node.name.value
        # Check if filed exists on model.
        if hasattr(qs.model, field_name):
            # Check if field has nested nodes.
            if field_node.selection_set:
                # Get model field.
                models_field = qs.model._meta.get_field(field_name)

                # Field has a select related relationship.
                if isinstance(models_field, (ForeignKey, OneToOneRel)):
                    model_relations['select_related'].append(field_name)

                # Field has a prefetch related relationship.
                if isinstance(models_field, (ManyToManyField, ManyToManyRel, ManyToOneRel)):
                    model_relations['prefetch_related'].append(field_name)

                # Prefix map
                prefix_nodes.append((field_name, field_node))

    # Extract and normalize paths representing relations betwean models.
    paths = extract_path(prefix_nodes)

    # Extract select_related and prefetch_related paths.
    select_related, prefetch_related = get_related(paths, model_relations)

    # Print related fields if they exist.
    if select_related or prefetch_related:
        print('SELECT_RELATED:', select_related)
        print('PREFETCH_RELATED:', prefetch_related)

    return qs.select_related(*select_related).prefetch_related(*prefetch_related)


def extract_path(nodes: list) -> set:
    """
    Function recursively extracts paths representing model relations extracted from graphql query.

    :param list nodes: List of FieldNodes. FieldNode is representing model to be extracted and added to model relation path.

    :return: set: Return set of strings containing paths of relations between models.
    """
    # sub_prefix is a temporary list to hold prefixes extracted from currently iterated node.
    sub_prefix = []
    new_paths = set()
    for prefix, field_node in nodes:
        # If field_node has nested models then loop over sub_node.
        if field_node.selection_set:
            for sub_node in field_node.selection_set.selections:
                # If sub_node has nested nodes create new prefix.
                if sub_node.selection_set:
                    new_prefix = prefix + '__' + sub_node.name.value
                    sub_prefix.append([new_prefix, sub_node])
                else:
                    new_paths.add(prefix)

    # Make recursive call only if there is data.
    if sub_prefix:
        nested_paths = extract_path(sub_prefix)
        new_paths.update(nested_paths)

    return new_paths


def get_related(paths: list, relation_prefixes: dict) -> tuple:
    """
    Function extracts select_related and prefetch_related paths from model prefix.
    Select related paths take precedence over prefetch related paths. It is because,
    it's faster to make SQL joins, and this is exactly what select_related does.

    :param list relations: Relations extracted from graphql query
    :param dict relation_prefixes: Dict that holds names of prefetch_related and select_related fields.

    :return: tuple: Returns a set of related fields. First element in tuple is select_related fields.
    Second element in tuple is prefetch_related fields.
    """
    select_related = set()
    prefetch_related = set()

    for relation in paths:
        # Construct select related fields for first path that starts with model name of related field.
        for srp in relation_prefixes['select_related']:
            if relation.startswith(srp):
                select_related.add(relation)
                break

        # Construct prefetch related fields for first path that starts with model name of related field.
        for prp in relation_prefixes['prefetch_related']:
            # Make sure that prefetched field does not exist in select related fields.
            if relation not in select_related and relation.startswith(prp):
                prefetch_related.add(relation)
                break

    return select_related, prefetch_related
