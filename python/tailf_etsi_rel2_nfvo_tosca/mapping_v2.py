from dict_utils import *


class V2Mapping:
    """
    See documentation/VDUMapping.md

    Mapping is strictly {DataLocationPath : LocationToPlaceDataPath}
    Which should almost always be {TOSCAPath : SOL6Path}
    """

    KEY_TOSCA = "dict_tosca"
    KEY_SOL6 = "dict_sol6"

    def __init__(self, dict_tosca, dict_sol6):
        self.dict_tosca = dict_tosca
        self.dict_sol6 = dict_sol6

    @staticmethod
    def map_ints(map1_list, start_num=0, **kwargs):
        """
        Example input: ["c1", "c2", "s3", "s4"], 0
        Example output: {"c1": 0, "c2": 1, "s3": 2, "s4": 3}
        :param map1_list: A list of strirngs
        :param start_num: The number to start mapping values to
        :return: A dict
        """
        result = []
        cur_num = start_num
        for item_1 in map1_list:
            try:
                if item_1 in result:
                    print("Dict slot {} is already full with {}".format(item_1, result[item_1]))

                result.append(MapElem(item_1, cur_num))
                cur_num += 1
            except KeyError:
                print("Key error")
        return result

    def generate_map(self, path, field_conditions, map_type="int", map_start=0,
                     map_function=None, map_args=None):
        """
        If map_function is not defined, look at map_type to determine what predefined mapping
        function to be used.
        Else, use the provided mapping function
        :param path:
        :param field_conditions:
        :param map_type:
        :param map_start:
        :param map_function:
        :param map_args:
        :return:
        """
        field = field_conditions[0]
        field_value = field_conditions[1]
        field_filter = None if len(field_conditions) < 3 else field_conditions[2]

        # Get the value at path
        p_val = get_path_value(path, self.dict_tosca)
        # Get the relevant nodes based on field and field_value
        filtered = get_roots_from_filter(p_val, field, field_value, user_filter=field_filter)

        return self.generate_map_from_list(filtered, map_type, map_start, map_function, map_args)

    def generate_map_from_list(self, to_map, map_type="int", map_start=0,
                               map_function=None, map_args=None):
        if not isinstance(to_map, list):
            raise TypeError("Expected type to be list, was {}".format(type(to_map)))

        # We now have a list of dicts
        # Get the names of each element in the lists
        names = []

        for elem in to_map:
            if not isinstance(elem, dict):
                raise TypeError("Expected type to be dict, was {}".format(type(elem)))

            names.append(get_dict_key(elem))

        mapped = None

        kwargs = {self.KEY_TOSCA: self.dict_tosca, self.KEY_SOL6: self.dict_sol6,
                  "filtered": to_map}
        if map_args:
            kwargs = merge_two_dicts(kwargs, map_args)

        # If there is a custom map function defined, use that instead of our defaults
        if map_function:
            mapped = map_function(names, map_start, **kwargs)
        else:
            if map_type == "int":
                mapped = V2Mapping.map_ints(names, map_start, **kwargs)
        return mapped

    @staticmethod
    def get_items_from_map(path, mapping, cur_dict):
        return [get_path_value(path.format(c_map.name), cur_dict) for c_map in mapping]

    @staticmethod
    def get_input_values(in_list, input_path, dict_tosca):
        tosca_inputs = get_path_value(input_path, dict_tosca)
        return [{item["get_input"]: V2Mapping.get_input_value(item, tosca_inputs=tosca_inputs)} for item in in_list]

    @staticmethod
    def get_input_value(item, input_path=None, dict_tosca=None, tosca_inputs=None):
        if input_path and dict_tosca and not tosca_inputs:
            tosca_inputs = get_path_value(input_path, dict_tosca)

        if V2Mapping.is_tosca_input(item):
            return tosca_inputs[item["get_input"]]

    @staticmethod
    def is_tosca_input(val):
        try:
            return "get_input" in val
        except TypeError:
            return False

    @staticmethod
    def tosca_get_input(input_name, tosca_inputs, dict_tosca):
        """
        Attempt to locate and return the value of the given input from the tosca vnf file
        :param tosca_inputs:
        :param dict_tosca:
        :param input_name: { 'get_input': 'VAR_NAME' }
        :returns: (var_name, data) or (None, None)
        """
        if not V2Mapping.is_tosca_input(input_name):
            return None, None

        template_inputs = get_path_value(tosca_inputs, dict_tosca)
        data = template_inputs[input_name["get_input"]]
        name = input_name["get_input"]

        return name, data


class MapElem:
    """

    """
    def __init__(self, name, cur_map, parent_map=None):
        self.name = name
        self.cur_map = cur_map
        self.parent_map = parent_map

    @staticmethod
    def format_path(elem, path, use_value=True):
        """
        Formats the provided path with the mapping that is stored internally
        Defaults to using the values of the mapping, but can be switched to use keys
        """

        path_list = path.split(".")
        while "{}" in path_list:
            # Get the index of the last occurrence of a formattable entry
            index = max(idx for idx, val in enumerate(path_list)
                        if val == '{}')

            val = elem.cur_map if use_value else elem.name
            path_list[index] = path_list[index].format(val)

            elem = elem.parent_map

        return ".".join(path_list)

    def __str__(self):
        return "{} -> {}, parent=({})".format(self.name, self.cur_map, self.parent_map)

    def __repr__(self):
        return self.__str__()
