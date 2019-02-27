"""
These are automatically used without having to update anything else.
The TOSCA variables are mapped to the SOL6 ones, they must have the same names.
The program does not attempt to map variables beginning with '_'
"""
from key_utils import KeyUtils
from mapping_v2 import *
from dict_utils import *
from list_utils import *


class TOSCA:

    @staticmethod
    @recfun
    def get_full_path(self, elem, dic):
        try:
            if not isinstance(dic[elem], list):
                return dic[elem]
        except KeyError:
            raise KeyError("Could not find {} as a parent".format(elem))

        return "{}.{}".format(self(dic[elem][0], dic), dic[elem][1])

    @staticmethod
    def set_variables(variables, dict_tosca, obj):
        """
        Take the input from the config file, and set the variables that are identifiers here
        This must be run before the values are used
        """
        tosca = variables["tosca"]
        key_list = V2Mapping.get_object_keys(obj, exclude="identifier")

        for k in key_list:
            set_val = False
            if "{}_VAL".format(k) in tosca:
                set_val = True

            if k not in tosca and not set_val:
                raise KeyError("{} does not exist in the configuration file".format(k))
            if set_val:
                val = dict_tosca[k]
            else:
                val = TOSCA.get_full_path(k, tosca)

            setattr(obj, k, val)


class SOL6:
    @staticmethod
    @recfun
    def get_full_path(self, elem, dic):
        try:
            if not isinstance(dic[elem], list):
                return dic[elem]
        except KeyError:
            raise KeyError("Could not find {} as a parent".format(elem))

        return "{}.{}".format(self(dic[elem][0], dic), dic[elem][1])


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


