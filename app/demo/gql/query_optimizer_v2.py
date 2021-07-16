import json
from collections import defaultdict

from django.db.models.query import QuerySet

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
FIXME: Uncomment mayor query and run the code. Fix this case!
FIXME: has_leaves set to False on deep nested leaves
TODO: Extract paths with has_leaves == False
TODO: Normalize paths to match django notation of related models (model1__model2__model3)
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

    def optimize(self, queryset: QuerySet) -> QuerySet:
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
                selections = self.info.field_nodes[0].selection_set.selections
                for idx, selection in enumerate(selections):
                    # Check if extracted field is a Type
                    if self.__filed_type(selection.name.value):
                        # Check for nested leaves inside selection
                        selections = self.info.field_nodes[0] \
                            .selection_set.selections[idx] \
                            .selection_set.selections

                        has_leaves = self.__selection_has_leaves(selections)

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
                section_has_leaves = any(leaves)
                if section_has_leaves:
                    has_leaves = True
                    iteration += 1

            # 2nd level of nesting
            if iteration == 1:
                print('Iteration', iteration)
                leaves = []
                first_iteration = iteration - 1
                for first_leaf_meta_field in paths[first_iteration]:
                    first_leaf_idx = first_leaf_meta_field['index']
                    selections = self.info.field_nodes[0] \
                        .selection_set.selections[first_leaf_idx] \
                        .selection_set.selections
                    for idx, selection in enumerate(selections):
                        if self.__filed_type(selection.name.value):
                            # Check for nested leaves inside selection
                            selections = self.info.field_nodes[0] \
                                .selection_set.selections[first_leaf_idx] \
                                .selection_set.selections[idx] \
                                .selection_set.selections
                            has_leaves = self.__selection_has_leaves(selections)

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
                section_has_leaves = any(leaves)
                if section_has_leaves:
                    has_leaves = True
                    iteration += 1

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
                                selections = self.info.field_nodes[0] \
                                    .selection_set.selections[first_leaf_idx] \
                                    .selection_set.selections[second_leaf_idx] \
                                    .selection_set.selections
                                for idx, selection in enumerate(selections):
                                    # Check for nested leaves inside selection
                                    has_leaves = self.__selection_has_leaves(selections)

                                    # Create metadata filed and add it to current iteration
                                    if self.__filed_type(selection.name.value):
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
                section_has_leaves = any(leaves)
                if section_has_leaves:
                    has_leaves = True
                    iteration += 1

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
                                    selections = self.info.field_nodes[0] \
                                        .selection_set.selections[first_leaf_idx] \
                                        .selection_set.selections[second_leaf_idx] \
                                        .selection_set.selections[third_leaf_idx] \
                                        .selection_set.selections
                                    for idx, selection in enumerate(selections):
                                        # Check for nested leaves inside selection
                                        has_leaves = self.__selection_has_leaves(selections)

                                        # Create metadata filed and add it to current iteration
                                        if self.__filed_type(selection.name.value):
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
                section_has_leaves = any(leaves)
                if section_has_leaves:
                    has_leaves = True
                    iteration += 1

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
                                        selections = self.info.field_nodes[0] \
                                            .selection_set.selections[first_leaf_idx] \
                                            .selection_set.selections[second_leaf_idx] \
                                            .selection_set.selections[third_leaf_idx] \
                                            .selection_set.selections[fourth_leaf_idx] \
                                            .selection_set.selections
                                        for idx, selection in enumerate(selections):
                                            # Check for nested leaves inside selection
                                            has_leaves = self.__selection_has_leaves(selections)

                                            # Create metadata filed and add it to current iteration
                                            if self.__filed_type(selection.name.value):
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
                section_has_leaves = any(leaves)
                if section_has_leaves:
                    has_leaves = True
                    iteration += 1

        print(json.dumps(paths, indent=2, sort_keys=False))
        return queryset

    def print_types(self):
        """Print all graphql types"""
        for k, v in self.info.schema.type_map.items():
            print('Types', k, v)

    def __selection_has_leaves(self, selections) -> bool:
        """Check if selection has leaves"""
        has_leaves = False
        for selection in selections:
            print('selection.name.value', selection.name.value)
            has_leaves = self.__filed_type(selection.name.value)
        return has_leaves

    def __filed_type(self, field_name) -> bool:
        """Check if field name has its Type"""
        field_name = field_name[0].upper() + field_name[1:] + 'Type'
        return field_name in self.info.schema.type_map.keys()
