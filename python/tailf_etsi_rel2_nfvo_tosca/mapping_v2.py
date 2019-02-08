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
        Inputs: list of strings,
        Example output: {"c1": 0, "c2": 1, "s3": 2, "s4": 3}
        :return: Dict
        """
        result = {}
        for item_1 in map1_list:
            try:
                if item_1 in result:
                    print("Dict slot {} is already full with {}".format(item_1, result[item_1]))

                result[item_1] = start_num
                start_num += 1
            except KeyError:
                print("Key error")
        return result

    def generate_map(self, path, field, field_value, map_type=int, map_start=0,
                     map_function=map_ints):
        """

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
        print(p_val)
        #return map_function.__func__(t)
        return 0

