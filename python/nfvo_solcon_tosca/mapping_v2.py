from dict_utils import *


class V2Mapping:
    """
    See documentation/VDUMapping.md

    Mapping is strictly {DataLocationPath : LocationToPlaceDataPath}
    Which should almost always be {TOSCAPath : SOL6Path}
    """

    KEY_TOSCA = "dict_tosca"
    KEY_SOL6 = "dict_sol6"

    def __init__(self, dict_tosca, dict_sol6, log=None):
        self.dict_tosca = dict_tosca
        self.dict_sol6 = dict_sol6
        self.log = log

    @staticmethod
    def parent_match(map1_list, start_num=0, **kwargs):
        """
        Given a list, like ['a', 'b', 'c'], then a value dict of
        {'a': 'apple', 'b': 'banana', 'c': 'carrot'}

        A parent map of
        [apple -> 0, banana -> 1, carrot -> 2]

        Return a mapping:
        [a -> apple, parent=(apple -> 0),
        b -> banana, parent=(banana-> 1),
        c -> carrot, parent=(carrot -> 2)]
        """
        if "parent_map" not in kwargs:
            raise KeyError("parent_map not included in kwargs")
        if "value_dict" not in kwargs:
            raise KeyError("value_dict not included in kwargs")
        value_dict = kwargs["value_dict"]
        parent_map = kwargs["parent_map"]

        result = []
        for key in map1_list:
            value = value_dict[key]
            final_parent_map = None

            # Find the element in the parent map that the cur element is mapped to
            # For example [c1_nic0 -> c1] and [c1 -> 0]
            for p_map in parent_map:
                if p_map.name == value:
                    final_parent_map = p_map
                    break

            map_elem = MapElem(key, value, final_parent_map)
            result.append(map_elem)

        return result

    @staticmethod
    def map_ints(map1_list, start_num=0, **kwargs):
        """
        Example input: ["c1", "c2", "s3", "s4"], 0
        Example output: {"c1": 0, "c2": 1, "s3": 2, "s4": 3}
        Options: parent_map, value_map, none_value, none_key
        :param map1_list: A list of strirngs
        :param start_num: The number to start mapping values to
        :optional parent_map:
        :optional value_map:
        :optional none_value:
        :optional none_key:
        :return: A dict of the mappings
        """
        parent_map = None
        if "parent_map" in kwargs:
            parent_map = kwargs["parent_map"]
        value_map = None
        if "value_map" in kwargs:
            value_map = kwargs["value_map"]
        none_value = kwargs["none_value"] if "none_value" in kwargs else False
        none_key = kwargs["none_key"] if "none_key" in kwargs else False

        result = []
        cur_num = start_num
        for item_1 in map1_list:
            try:
                if item_1 in result:
                    log.info("Dict slot {} is already full with {}".format(item_1, result[item_1]))

                # We need to find the parent mapping so we can include it in the map definition
                final_parent_map = None
                if parent_map:
                    # Find the element in the parent map that the cur element is mapped to
                    # For example [c1_nic0 -> c1] and [c1 -> 0]
                    for p_map in parent_map:
                        if p_map.name == item_1:
                            final_parent_map = p_map
                            break
                elif value_map:
                    for v_map in value_map:
                        if v_map.name == cur_num:
                            final_parent_map = v_map
                            break
                cur_num_val = None if none_value else cur_num
                cur_item_1 = None if none_key else item_1
                map_elem = MapElem(cur_item_1, cur_num_val, final_parent_map)

                result.append(map_elem)
                cur_num += 1
            except KeyError:
                log.error("Key error")
        return result

    def generate_map(self, path, field_conditions, map_type="int", map_start=0,
                     map_function=None, map_args=None, cur_dict=None, parent=None):
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
        :param cur_dict: If we are only specifying the path to generate a mapping, specify the dict
        to read from
        :param parent: Parent MapElem to assign, if it doesn't exist
        :return:
        """
        field = None
        field_value = None
        field_filter = None
        if field_conditions:
            field = field_conditions[0]
            field_value = field_conditions[1]
            field_filter = None if len(field_conditions) < 3 else field_conditions[2]

        # Get the value at path
        if path:
            p_val = get_path_value(path, self.dict_tosca, ensure_dict=True)
        else:
            # If there is no path, search the entire dict
            p_val = self.dict_tosca

        # Get the relevant nodes based on field and field_value
        filtered = None
        if field and field_value:
            filtered = get_roots_from_filter(p_val, field, field_value, user_filter=field_filter)
        elif path:
            # If we do not have field & field_value, but we do have path
            filtered = get_path_value(path, cur_dict)
            if not isinstance(filtered, list):
                filtered = [filtered]

        result = self.generate_map_from_list(filtered, map_type, map_start, map_function, map_args)
        if parent:
            # We can't overwrite parent mappings, but there might be some, so just don't do anything
            # if that is the case
            MapElem.add_parent_mapping(result, parent, fail_silent=True)

        return result

    def generate_map_from_list(self, to_map, map_type="int", map_start=0,
                               map_function=None, map_args=None):
        if not isinstance(to_map, list):
            raise TypeError("Expected type to be list, was {}".format(type(to_map)))

        # We now have a list of dicts
        # Get the names of each element in the lists
        names = []

        for elem in to_map:
            if isinstance(elem, dict):
                names.append(get_dict_key(elem))
            elif isinstance(elem, str):
                names.append(elem)
            elif isinstance(elem, tuple):
                names.append(elem[0])
            else:
                raise TypeError("Unhandled type {}".format(type(elem)))

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
            elif map_type == "parent_match":
                mapped = V2Mapping.parent_match(names, map_start, **kwargs)
        return mapped

    @staticmethod
    def get_items_from_map(path, mapping, cur_dict, link_list=False):
        res = [get_path_value(path.format(c_map.name), cur_dict) for c_map in mapping]
        # We need the VDU names that are linked with the flavors, so get them this way
        if link_list:
            temp = []
            for i, c_map in enumerate(mapping):
                temp.append([c_map.name, res[i]])
            res = temp
        return res

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
    def tosca_get_input_key(input_name):
        if V2Mapping.is_tosca_input(input_name):
            return input_name["get_input"]

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

    @staticmethod
    def get_object_keys(obj, exclude=None):
        return [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and
                not (attr.startswith("__") or attr.startswith("_") or
                     (exclude and exclude in attr))]


class MapElem:
    """

    """
    def __init__(self, name, cur_map, parent_map=None):
        self.name = name
        self.cur_map = cur_map
        self.parent_map = parent_map

    def copy(self):
        par = self.parent_map.copy() if self.parent_map else None
        return MapElem(self.name, self.cur_map, par)

    @staticmethod
    def ensure_map_values(mapping):
        """
        Given a mapping, ensure that the values are properly incrementing, if not fix them.
        Only applies to top-level mapping, does not check parent maps
        """
        # If it's valid, don't do anything
        if MapElem.validate_map_values(mapping):
            return
        # Take the first value and increment from there
        cur_val = mapping[0].cur_map
        for c_map in mapping:
            c_map.cur_map = cur_val
            cur_val += 1

    @staticmethod
    def validate_map_values(mapping):
        """
        Ensure the values are incrementing by 1 each time, if not return False
        """
        if not isinstance(mapping, list):
            return True
        last_value = None
        for c_map in mapping:
            if last_value is None:
                last_value = c_map.cur_map
            else:
                if last_value != c_map.cur_map + 1:
                    return False
        return True

    @staticmethod
    def add_parent_mapping(mapping_list, parent_mapping, fail_silent=False):
        if not isinstance(mapping_list, list):
            mapping_list = [mapping_list]
        for c_map in mapping_list:
            if c_map.parent_map:
                if fail_silent:
                    log.debug("SILENT: Expected an empty parent map, instead found {}".
                              format(c_map.parent_map))
                    continue
                raise KeyError("Expected an empty parent map, instead found {}".
                               format(c_map.parent_map))
            if not isinstance(parent_mapping, MapElem):
                raise ValueError("Expected a MapElem, instead {} was given".
                                 format(type(parent_mapping)))
            c_map.parent_map = parent_mapping

    @staticmethod
    def basic_map(num):
        return MapElem(num, num)

    @staticmethod
    def basic_map_list(num):
        return [MapElem.basic_map(n) for n in range(num)]

    @staticmethod
    def format_path(elem, path, use_value=True):
        """
        Formats the provided path with the mapping that is stored internally
        Defaults to using the values of the mapping, but can be switched to use keys
        If the value of a mapping is None, it will not be formatted into the string.
        This allows different numbers of formattable elements.
        """

        path_list = path.split(".")
        while "{}" in path_list:
            # Get the index of the last occurrence of a formattable entry
            index = max(idx for idx, val in enumerate(path_list)
                        if val == '{}')
            if elem:
                val = elem.cur_map if use_value else elem.name
            else:
                val = ""
                # Skip the given value if it's None
            if val is not None:
                path_list[index] = path_list[index].format(val)

            if not elem:
                break

            elem = elem.parent_map

        return ".".join(path_list)

    def __str__(self):
        return "{} -> {}, parent=({})".format(self.name, self.cur_map, self.parent_map)

    def __repr__(self):
        return self.__str__()

