from dict_utils import *

class V2Mapping:
    """
    See documentation/VDUMapping.md

    Mapping is strictly {DataLocationPath : LocationToPlaceDataPath}
    Which should almost always be {TOSCAPath : SOL6Path}
    """

    def __init__(self, dict_tosca, dict_sol6):
        self.dict_tosca = dict_tosca
        self.dict_sol6 = dict_sol6

    @staticmethod
    def map_ints(map1_list, start_num=0):
        """
        Example input: ["c1", "c2", "s3", "s4"], 0
        Example output: {"c1": 0, "c2": 1, "s3": 2, "s4": 3}
        :param map1_list: A list of strirngs
        :param start_num: The number to start mapping values to
        :return: A dict
        """
        result = {}
        cur_num = start_num
        for item_1 in map1_list:
            try:
                if item_1 in result:
                    print("Dict slot {} is already full with {}".format(item_1, result[item_1]))

                result[item_1] = cur_num
                cur_num += 1
            except KeyError:
                print("Key error")
        return result

    def generate_map(self, path, field, field_value, map_type=int, map_start=0,
                     map_function=None):
        """
        If map_function is not defined, look at map_type to determine what predefined mapping
        function to be used.
        Else, use the provided mapping functoin
        :param path:
        :param field:
        :param field_value:
        :param map_type:
        :param map_start:
        :param map_function:
        :return:
        """

        # Get the value at path
        p_val = get_path_value(path, self.dict_tosca)
        # Get the relevant nodes based on field and field_value
        filtered = get_roots_from_filter(p_val, field, field_value)

        if not isinstance(filtered, list):
            raise TypeError("Expected type to be list, was {}".format(type(filtered)))

        # We now have a list of dicts
        # Get the names of each element in the lists
        names = []

        for elem in filtered:
            if not isinstance(elem, dict):
                raise TypeError("Expected type to be dict, was {}".format(type(elem)))

            names.append(get_dict_key(elem))

        mapped = None

        if map_function:
            mapped = map_function(names, map_start)
        else:
            if map_type is int:
                mapped = V2Mapping.map_ints(names, map_start)

        return mapped

