class GQOptimizer():

    def __init__(self, info):
        self.info = info
        self.gql_query = info.field_nodes[0].loc.source.body

    def optimize(self, queryset):
        qs_info = {queryset.model.__name__ : []}
        print(self.gql_query)

        for k, v in self.info.schema.type_map.items():
            print(k, v)

        if self.gql_query.count('{') - 1 >= 2:
            template = {
                'level': 0,
                'only': [],
                'prefetch_related': [],
                'select_related': [],
            }
            for selection in self.info.field_nodes[0].selection_set.selections:
                field_name = selection.loc.start_token.value
                field_type = self.__field_name_to_type(field_name)
                match = self.__has_type(field_type)
                if not self.__has_type(field_type):
                    template['only'].append(field_name)
                else:
                    template['only'].append(field_name + '_id')
                    template['select_related'].append(field_name)

            qs_info[queryset.model.__name__] = template
            print('>>> A', field_name, field_type, match)

        if self.gql_query.count('{') - 1 >= 3:
            for selection in self.info.field_nodes[0].selection_set.selections[-1].selection_set.selections:
                field_name = selection.loc.start_token.value
                field_type = self.__field_name_to_type(field_name)
                match = self.__has_type(field_type)
                print('>>> B', field_name, field_type, match)

        if self.gql_query.count('{') - 1 >= 4:
            for selection in self.info.field_nodes[0].selection_set.selections[-1].selection_set.selections[-1].selection_set.selections:
                field_name = selection.loc.start_token.value
                field_type = self.__field_name_to_type(field_name)
                match = self.__has_type(field_type)
                print('>>> C', field_name, field_type, match)

        print('QS INFO', qs_info)
        return queryset


    def __get_type(self, name):
        return self.info.schema.type_map[name]


    def __has_type(self, name):
        return name in self.info.schema.type_map.keys()


    def __field_name_to_type(self, name):
        return name[0].upper() + name[1:] + 'Type'
