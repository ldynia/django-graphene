def optimizer(qs, info):
    """ """
    print('=============================')
    # print(info)
    # from graphql.execution.execute import get_field_def
    # field_def = get_field_def(info.schema, info.parent_type, info.field_name)
    # field_type = _get_type(field_def)
    # graphene_type = field_type.graphene_type

    # model = field_type.graphene_type._meta.model
    # print(qs.model)
    model = qs.model
    top_node = info.field_nodes[0]

    prefetch_fields, selected_fields = optimization_fields(top_node, model)

    print('=============================')
    print(prefetch_fields)
    print(selected_fields)
    print('=============================')

    return qs.prefetch_related(*prefetch_fields).select_related(*selected_fields)

from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related import ManyToManyField
from django.db.models.fields.reverse_related import ManyToManyRel
from django.db.models.fields.reverse_related import ManyToOneRel


def optimization_fields(field_node, model, prefix=''):
    """

    :param field_node: [description]
    :param model: [description]
    :param prefix: [description]

    :return: [description]
    """
    # The fields for the optimization.
    prefetch_fields = []
    selected_fields = []

    # Loop over sub-nodes of the field-node.
    for sub_node in field_node.selection_set.selections:
        # Get field name.
        node_name = sub_node.name.value

        # Check if the node is a model field.
        if hasattr(model, node_name):
            # Get model-field.
            field = model._meta.get_field(node_name)

            # Add ForeignKey-fields to select-fields
            if prefix == '' and isinstance(field, (ForeignKey)):
                selected_fields.append(prefix + node_name)

            # Add ManyTo-fields to prefetch-fields.
            elif isinstance(field, (ForeignKey, ManyToOneRel, ManyToManyRel, ManyToManyField)):
                prefetch_fields.append(prefix + node_name)

            # Update prefix and model.
            new_prefix = prefix + node_name + '__'
            new_model = field.related_model

        else:
            # Use existing prefix and model.
            new_prefix = prefix
            new_model = model

        # Go deeper if node has additional node.
        if sub_node.selection_set:
            #
            nested_fields = optimization_fields(sub_node, new_model, new_prefix)
            prefetch_fields += nested_fields[0]
            selected_fields += nested_fields[1]

    return prefetch_fields, selected_fields
