from collections import Counter
from django.core.exceptions import FieldError

"""
query AllCities {
  allCities {
    id
    name
    state {
      name
    }
    # mayor {
    #   firstName
    #   city {
    #     id
    #     name
    #   }
    # }
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
query AllCities {
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
"""

"""
query AllCities {
  allCities {
    name
    district {
      name
    }
    state {
      name
      country {
        name
        continent {
          name
        }
      }
    }
    district {
      name
      city {
        name
      }
    }
  }
}
"""

def optimizer(qs, info):
    model = qs.model
    top_node = info.field_nodes[0]

    relations = []
    for field in top_node.selection_set.selections:
        field_name = field.name.value
        # Check if field has nested models
        if field.selection_set:
            prefix = optimization_fields(field, field_name)
            relations.append(prefix)

    print('relations before', relations)
    relations = normalize_paths(relations)
    print('relations after ', relations)

    select_related, prefetch_related = get_related(model, relations)

    print('select_related', select_related)
    print('prefetch_related', prefetch_related)

    return qs.select_related(*select_related).prefetch_related(*prefetch_related)


def optimization_fields(field_node, prefix=''):
    if field_node.selection_set:
        for sub_node in field_node.selection_set.selections:
            if sub_node.selection_set:
                prefix = prefix + '__' + sub_node.name.value
                return optimization_fields(sub_node, prefix)
    return prefix


def get_related(model, relations: list) -> tuple:
    select_related = set()
    prefetch_related = set()

    for relation in relations:
        try:
            model.objects.select_related(relation).first()
            select_related.add(relation)
        except FieldError as err:
            print('Error in select_related:', err)

        if relation not in select_related:
            try:
                model.objects.prefetch_related(relation).first()
                prefetch_related.add(relation)
            except FieldError as err:
                print('Error in prefetch_related:', err)

    return select_related, prefetch_related


def normalize_paths(paths: list):
    normalized_paths = []
    for path in paths:
        models = path.split('__')
        if len(models) == 1:
            normalized_paths.append(path)
        else:
            models_count = dict(Counter(models))
            for model, count in models_count.items():
                if count >= 2:
                    path = model.join(path.split(model, 2)[:2])
                    path = path.strip('_')
            normalized_paths.append(path)
    return normalized_paths
