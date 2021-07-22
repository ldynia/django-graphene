import json
from collections import Counter
from collections import defaultdict

from django.db.models.query import QuerySet
from django.core.exceptions import FieldError
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

# FIXME: Uncomment mayor query and run the code. Fix this case!

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

    def optimize(self, queryset: QuerySet, stop_fields=[]) -> QuerySet:
        self.stop_fields = stop_fields

        paths = self.__extract_paths()
        print('before normalization', paths)
        if self.stop_fields:
            paths = self.__normalize_paths(paths)
        print('normalized paths', paths)

        select_related = []
        prefetch_related = []
        for path in paths:
            # Get first model fro the model relations path
            first_model = path
            if '__' in path:
                first_model = path.split('__')[0]

            # Extract filed from first model
            field = queryset.model._meta.get_field(first_model)

            # Select related models
            if isinstance(field, (ForeignKey, ManyToManyField, OneToOneRel)):
                select_related.append(path)

            # Prefetch related models
            if isinstance(field, (ManyToOneRel, ManyToManyRel)):
                if path not in select_related:
                    prefetch_related.append(path)

        print(f'Select related: {select_related}')
        if select_related:
            queryset = queryset.select_related(*select_related)

        print(f'Prefetch_related: {prefetch_related}')
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)

        return queryset

    def print_types(self):
        """Print all graphql types"""
        for k, v in self.info.schema.type_map.items():
            print('Types', k, v)

    def __normalize_paths(self, paths: list):
        normalized_paths = []
        for stop_field in self.stop_fields:
            for path in paths:
                path = path.replace(stop_field, '')
                path = path.strip('_')
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

    def __extract_paths(self):
        root = self.info.field_name
        paths = defaultdict(list)

        iteration = 0
        has_leaves = True
        while has_leaves:
            has_leaves = False

            # 1st level on nesting
            if iteration == 0:
                print('Iteration', iteration)
                leaves = []
                # Extract fields from root of the query
                selection_set = self.info.field_nodes[0].selection_set
                for idx, selection in enumerate(selection_set.selections):
                    # Check if extracted field is a Type
                    if self.__filed_type(selection.name.value):
                        # Check for nested leaves inside selection
                        selection_set = self.info.field_nodes[0] \
                            .selection_set.selections[idx] \
                            .selection_set

                        # has_leaves = self.__selection_has_leaves(selections)
                        has_leaves = self.__selection_has_leaves(selection_set)

                        # Create metadata filed
                        paths[iteration].append({
                            'has_leaves': has_leaves,
                            'index': idx,
                            'root': root,
                            'parent': root,
                            'field_name': selection.name.value,
                            'selection': root + '__' + selection.name.value
                        })
                        leaves.append(True)
                    else:
                        leaves.append(False)

                # Check that leaves exist
                has_leaves, iteration = self.__increment(iteration, leaves)

            # 2nd level of nesting
            if iteration == 1:
                print('Iteration', iteration)
                leaves = []
                first_iteration = iteration - 1
                for first_leaf_meta_field in paths[first_iteration]:
                    first_leaf_idx = first_leaf_meta_field['index']
                    selection_set = self.info.field_nodes[0] \
                        .selection_set.selections[first_leaf_idx] \
                        .selection_set
                    for idx, selection in enumerate(selection_set.selections):
                        if self.__filed_type(selection.name.value):
                            # Check for nested leaves inside selection
                            selection_set = self.info.field_nodes[0] \
                                .selection_set.selections[first_leaf_idx] \
                                .selection_set.selections[idx] \
                                .selection_set

                            has_leaves = self.__selection_has_leaves(selection_set)

                            # Create metadata filed and add it to current iteration
                            paths[iteration].append({
                                'has_leaves': has_leaves,
                                'index': idx,
                                'root': root,
                                'parent': first_leaf_meta_field['field_name'],
                                'field_name': selection.name.value,
                                'selection': first_leaf_meta_field['selection'] + '__' + selection.name.value
                            })
                            leaves.append(True)
                        else:
                            leaves.append(False)

                # Check that leaves exist
                has_leaves, iteration = self.__increment(iteration, leaves)

            # 3rd level of nesting
            if iteration == 2:
                print('Iteration', iteration)
                leaves = []
                first_iteration = iteration - 2
                second_iteration = iteration - 1
                for first_leaf_meta_field in paths[first_iteration]:
                    first_leaf_idx = first_leaf_meta_field['index']
                    if first_leaf_meta_field['has_leaves']:
                        for second_leaf_meta_field in paths[second_iteration]:
                            second_leaf_idx = second_leaf_meta_field['index']
                            if second_leaf_meta_field['has_leaves']:
                                selection_set = self.info.field_nodes[0] \
                                    .selection_set.selections[first_leaf_idx] \
                                    .selection_set.selections[second_leaf_idx] \
                                    .selection_set
                                for idx, selection in enumerate(selection_set.selections):
                                    # Create metadata filed and add it to current iteration
                                    if self.__filed_type(selection.name.value):
                                        selection_set = self.info.field_nodes[0] \
                                            .selection_set.selections[first_leaf_idx] \
                                            .selection_set.selections[second_leaf_idx] \
                                            .selection_set.selections[idx] \
                                            .selection_set

                                        # Check for nested leaves inside selection
                                        has_leaves = self.__selection_has_leaves(selection_set)

                                        paths[iteration].append({
                                            'has_leaves': has_leaves,
                                            'index': idx,
                                            'root': root,
                                            'parent': second_leaf_meta_field['field_name'],
                                            'field_name': selection.name.value,
                                            'selection': second_leaf_meta_field['selection'] + '__' + selection.name.value
                                        })
                                        leaves.append(True)
                                    else:
                                        leaves.append(False)
                # Check that leaves exist
                has_leaves, iteration = self.__increment(iteration, leaves)

            # 4th level of nesting
            if iteration == 3:
                print('Iteration', iteration)
                leaves = []
                first_iteration = iteration - 3
                second_iteration = iteration - 2
                third_iteration = iteration - 1
                for first_leaf_meta_field in paths[first_iteration]:
                    first_leaf_idx = first_leaf_meta_field['index']
                    if first_leaf_meta_field['has_leaves']:
                        for second_leaf_meta_field in paths[second_iteration]:
                            second_leaf_idx = second_leaf_meta_field['index']
                            for third_leaf_meta_field in paths[third_iteration]:
                                third_leaf_idx = third_leaf_meta_field['index']
                                if third_leaf_meta_field['has_leaves']:
                                    selection_set = self.info.field_nodes[0] \
                                        .selection_set.selections[first_leaf_idx] \
                                        .selection_set.selections[second_leaf_idx] \
                                        .selection_set.selections[third_leaf_idx] \
                                        .selection_set
                                    for idx, selection in enumerate(selection_set.selections):
                                        # Create metadata filed and add it to current iteration
                                        if self.__filed_type(selection.name.value):
                                            selection_set = self.info.field_nodes[0] \
                                                .selection_set.selections[first_leaf_idx] \
                                                .selection_set.selections[second_leaf_idx] \
                                                .selection_set.selections[third_leaf_idx] \
                                                .selection_set.selections[idx] \
                                                .selection_set

                                            # Check for nested leaves inside selection
                                            has_leaves = self.__selection_has_leaves(selection_set)

                                            paths[iteration].append({
                                                'has_leaves': has_leaves,
                                                'index': idx,
                                                'root': root,
                                                'parent': third_leaf_meta_field['field_name'],
                                                'field_name': selection.name.value,
                                                'selection': third_leaf_meta_field['selection'] + '__' + selection.name.value
                                            })
                                            leaves.append(True)
                                        else:
                                            leaves.append(False)
                # Check that leaves exist
                has_leaves, iteration = self.__increment(iteration, leaves)

            # 5th level of nesting
            if iteration == 4:
                print('Iteration', iteration)
                leaves = []
                first_iteration = iteration - 4
                second_iteration = iteration - 3
                third_iteration = iteration - 2
                fourth_iteration = iteration - 1
                for first_leaf_meta_field in paths[first_iteration]:
                    first_leaf_idx = first_leaf_meta_field['index']
                    if first_leaf_meta_field['has_leaves']:
                        for second_leaf_meta_field in paths[second_iteration]:
                            second_leaf_idx = second_leaf_meta_field['index']
                            for third_leaf_meta_field in paths[third_iteration]:
                                third_leaf_idx = third_leaf_meta_field['index']
                                for fourth_leaf_meta_field in paths[fourth_iteration]:
                                    fourth_leaf_idx = fourth_leaf_meta_field['index']
                                    if third_leaf_meta_field['has_leaves']:
                                        selection_set = self.info.field_nodes[0] \
                                            .selection_set.selections[first_leaf_idx] \
                                            .selection_set.selections[second_leaf_idx] \
                                            .selection_set.selections[third_leaf_idx] \
                                            .selection_set.selections[fourth_leaf_idx] \
                                            .selection_set
                                        for idx, selection in enumerate(selection_set.selections):
                                            # Create metadata filed and add it to current iteration
                                            if self.__filed_type(selection.name.value):
                                                selection_set = self.info.field_nodes[0] \
                                                    .selection_set.selections[first_leaf_idx] \
                                                    .selection_set.selections[second_leaf_idx] \
                                                    .selection_set.selections[third_leaf_idx] \
                                                    .selection_set.selections[fourth_leaf_idx] \
                                                    .selection_set.selections[idx] \
                                                    .selection_set

                                                # Check for nested leaves inside selection
                                                has_leaves = self.__selection_has_leaves(selection_set)

                                                paths[iteration].append({
                                                    'has_leaves': has_leaves,
                                                    'index': idx,
                                                    'root': root,
                                                    'parent': fourth_leaf_meta_field['field_name'],
                                                    'field_name': selection.name.value,
                                                    'selection': fourth_leaf_meta_field['selection'] + '__' + selection.name.value
                                                })
                                                leaves.append(True)
                                            else:
                                                leaves.append(False)
                # Check that leaves exist
                has_leaves, iteration = self.__increment(iteration, leaves)

        print(json.dumps(paths, indent=2, sort_keys=False))

        filtered_paths = set()
        for paths in paths.values():
            for field in paths:
                if not field['has_leaves']:
                    filtered_paths.add(field['selection'])

        return filtered_paths

    def __increment(self, iteration: int, leaves: list) -> tuple:
        """Check that section_has leaves"""
        has_leaves = any(leaves)
        if has_leaves:
            iteration += 1
        return (has_leaves, iteration)

    def __selection_has_leaves(self, selection_set) -> bool:
        """Check if selection has leaves"""
        selection = self.gql_query[selection_set.loc.start:selection_set.loc.end]
        return selection.count('{') >= 2

    def __filed_type(self, field_name) -> bool:
        """Check if field name has its Type"""
        field_name = field_name[0].upper() + field_name[1:] + 'Type'
        return field_name in self.info.schema.type_map.keys()
