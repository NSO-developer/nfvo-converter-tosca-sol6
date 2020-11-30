"""
These are automatically used without having to update anything else.
The TOSCA variables are mapped to the SOL6 ones, they must have the same names.
The program does not attempt to map variables beginning with '_'
"""
from mapping_v2 import *
import logging
log = logging.getLogger(__name__)


class PathMapping:
    @staticmethod
    def format_paths(variables):
        """
        Pass in the inputs variable, then create the full paths for 'tosca' and 'sol6'
        If _VAL is at the end of the variable, don't process the path, just set the variable to
        the value.
        """
        var_tosca = variables["tosca"]
        var_sol6 = variables["sol6"]
        processed_tosca = {}
        processed_sol6 = {}

        for k in var_tosca:
            if "_VAL" not in k:
                val = PathMapping.get_full_path(k, var_tosca)
            else:
                val = var_tosca[k]
            processed_tosca[k] = val

        for k in var_sol6:
            if "_VAL" not in k:
                val = PathMapping.get_full_path(k, var_sol6)
            else:
                val = var_sol6[k]
            processed_sol6[k] = val
        variables["tosca"] = processed_tosca
        variables["sol6"] = processed_sol6
        return variables

    @staticmethod
    def set_variables(cur_dict, obj, exclude=""):
        """
        This is deprecated

        Take the input from the config file, and set the variables that are identifiers here
        This must be run before the values are used
        """
        key_list = V2Mapping.get_object_keys(obj, exclude=exclude)

        for k in key_list:
            var_val = "{}_VAL".format(k)
            set_val = True if var_val in cur_dict else False

            if k not in cur_dict and not set_val:
                log.error("{} does not exist in the configuration file".format(k))
            if set_val:
                val = cur_dict[var_val]
            else:
                val = PathMapping.get_full_path(k, cur_dict)

            setattr(obj, k, val)

    @staticmethod
    def get_full_path(elem, dic):
        try:
            if not isinstance(dic[elem], list):
                return dic[elem]
        except KeyError:
            log.error("Could not find {} as a parent".format(elem))
            return ""

        return "{}{}{}".format(PathMapping.get_full_path(dic[elem][0], dic), SPLIT_CHAR, dic[elem][1])


class TOSCA_BASE(PathMapping):
    pass


class SOL6_BASE(PathMapping):
    pass


class V2MapBase(V2Mapping):
    """

    """
    FLAG_BLANK                      = ""
    # Pass this flag if you want to set the value with the key and not the value
    FLAG_KEY_SET_VALUE              = "KSV"
    # Will remove all non-numeric characters
    FLAG_ONLY_NUMBERS               = "NUMBERS"
    FLAG_ONLY_NUMBERS_FLOAT         = "NUMBERSFLOAT"
    FLAG_MIN_1                      = "MINVAL1"
    # Make the tosca MapElem format use the value of the mapping instead of the key
    FLAG_USE_VALUE                  = "USESOLMAPFORTOSCA"
    # Append the items to a list, create the list if it doesn't exist
    FLAG_APPEND_LIST                = "APPENDLIST"
    # Get the first element in the output list
    FLAG_LIST_FIRST                 = "GETFIRSTLISTELEM"
    FLAG_LIST_NTH                   = "GETNTHLISTELEM"
    # Require delta validation
    FLAG_REQ_DELTA                  = "YAMLSUCKS"
    # Try to format the value as a valid input for layer-protocol
    FLAG_FORMAT_IP                  = "FORMATIPVER"
    FLAG_FORMAT_DISK_FMT            = "FORMATDISK"
    FLAG_FORMAT_CONT_FMT            = "FORMATCONTAINER"
    FLAG_FORMAT_AFF_SCOPE           = "FORMATAFFSCOPE"
    FLAG_FORMAT_STORAGE_TYPE        = "FORMATSTORAGETYPE"
    # If a value is getting formatted, return None instead of default 'val (INVALID)'
    FLAG_FORMAT_INVALID_NONE        = "INVALIDISNONE"

    # Label if this is a variable output
    # This means if the value to set is an input, to set it, if it is not an input, don't set
    # anything
    FLAG_VAR                        = "THISVARIABLE"
    # Marks this as requiring a value, and if there isn't one, make it 'root'
    FLAG_TYPE_ROOT_DEF              = "MUSTBESOMETHINGORROOT"
    # Suppress any error or warning messages relating to this mapping
    FLAG_FAIL_SILENT                = "FAILSIILENT"
    # Throw an error/warning if this mapping element doesn't have a parent
    FLAG_REQ_PARENT                 = "REQPARENT"
    # Specify if the output unit is in GBs, will attempt to convert to MBs
    # This flag implies FLAG_ONLY_NUMBERS_FLOAT
    FLAG_UNIT_GB                    = "UNITISGB"
    FLAG_UNIT_FRACTIONAL            = "UNITISFRACTIONAL"

    def __init__(self, dict_tosca, dict_sol6, c_log=None, variables=None):
        super().__init__(dict_tosca, dict_sol6)
        self.va_s = None
        self.va_t = None
        self.mapping = []

        if variables:
            self.va_t = variables["tosca"]
            self.va_s = variables["sol6"]

    def add_map(self, cur_map):
        self.mapping.append(cur_map)

    @staticmethod
    def set_value(val, path, index, prefix_value=None, prefix_index=None):
        _mapping = MapElem(val, index)
        if prefix_value is not None or prefix_index is not None:
            _mapping = MapElem(prefix_value, prefix_index, parent_map=_mapping)
        return (val, V2MapBase.FLAG_KEY_SET_VALUE), [path, [_mapping]]

    def get_tosca_value(self, value):
        return self.get_value(value, self.va_t, "tosca")

    def get_sol6_value(self, value):
        return self.get_value(value, self.va_s, "sol6")

    @staticmethod
    def get_value(value, dic, cfile="unspecified"):
        """
        Handle missing keys in here so the external program doesn't crash when exceptions are thrown
        """
        try:
            return dic[value]
        except KeyError:
            log.warning("Key '{}' not found in '{}' config file".format(value, cfile))
