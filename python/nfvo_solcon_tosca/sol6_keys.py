"""
These are automatically used without having to update anything else.
The TOSCA variables are mapped to the SOL6 ones, they must have the same names.
The program does not attempt to map variables beginning with '_'
"""
from mapping_v2 import *


class PathMaping:
    @staticmethod
    def set_variables(cur_dict, obj, exclude=""):
        """
        Take the input from the config file, and set the variables that are identifiers here
        This must be run before the values are used
        """

        key_list = V2Mapping.get_object_keys(obj, exclude=exclude)

        for k in key_list:
            var_val = "{}_VAL".format(k)
            set_val = True if var_val in cur_dict else False

            if k not in cur_dict and not set_val:
                raise KeyError("{} does not exist in the configuration file".format(k))
            if set_val:
                val = cur_dict[var_val]
            else:
                val = PathMaping.get_full_path(k, cur_dict)

            setattr(obj, k, val)

    @staticmethod
    def get_full_path(elem, dic):
        try:
            if not isinstance(dic[elem], list):
                return dic[elem]
        except KeyError:
            raise KeyError("Could not find {} as a parent".format(elem))

        return "{}.{}".format(PathMaping.get_full_path(dic[elem][0], dic), dic[elem][1])


class TOSCA_BASE(PathMaping):
    pass


class SOL6_BASE(PathMaping):
    pass


class V2Map(V2Mapping):
    """

    """
    FLAG_BLANK                      = ""
    # Pass this flag if you want to set the value with the key and not the value
    FLAG_KEY_SET_VALUE              = "KSV"
    # Will remove all non-numeric characters
    FLAG_ONLY_NUMBERS               = "NUMBERS"
    FLAG_ONLY_NUMBERS_FLOAT         = "NUMBERSFLOAT"
    # Make the tosca MapElem format use the value of the mapping instead of the key
    FLAG_USE_VALUE                  = "USESOLMAPFORTOSCA"
    # Append the items to a list, create the list if it doesn't exist
    FLAG_APPEND_LIST                = "APPENDLIST"
    # Get the first element in the input list
    FLAG_LIST_FIRST                 = "GETFIRSTLISTELEM"
    # Require delta validation
    FLAG_REQ_DELTA                  = "YAMLSUCKS"
    # Try to format the value as a valid input for layer-protocol
    FLAG_FORMAT_IP                  = "FORMATIPVER"
    # Label if this is a variable output
    # This means if the value to set is an input, to set it, if it is not an input, don't set
    # anything
    FLAG_VAR                        = "THISVARIABLE"
    # Marks this as requiring a value, and if there isn't one, make it 'root'
    FLAG_TYPE_ROOT_DEF              = "MUSTBESOMETHINGORROOT"

    mapping = {}

    def __init__(self, dict_tosca, dict_sol6, log=None):
        super().__init__(dict_tosca, dict_sol6, log)


