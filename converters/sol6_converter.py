import re
from keys.sol6_keys import *
from utils.dict_utils import *
from utils.key_utils import KeyUtils
import logging
log = logging.getLogger(__name__)


class Sol6Converter:
    tosca_vnf = None
    parsed_dict = None
    vnfd = None
    keys = None

    def __init__(self, tosca_vnf, parsed_dict, variables=None):
        self.tosca_vnf = tosca_vnf
        self.parsed_dict = parsed_dict
        self.variables = variables

        # Set this up for _virtual_get_flavor_names
        self.run_deltas = True
        # If we want to hard skip the loop that runs the deltas
        self.override_run_deltas = False

        # Set up the flag variables
        self.key_as_value       = False
        self.only_number        = False
        self.only_number_float  = False
        self.append_list        = False
        self.first_list_elem    = False
        self.nth_list_elem      = False
        self.tosca_use_value    = False
        self.format_as_ip       = False
        self.format_as_disk     = False
        self.format_as_container = False
        self.format_as_aff_scope = False
        self.format_as_storage = False
        self.format_invalid_none = False
        self.fail_silent        = False
        self.req_parent         = False
        self.first_list_output  = False
        self.unit_gb            = False
        self.unit_fractional    = False
        self.min_1              = False

    def convert(self, provider=None):
        """
        For overriding
        Convert the tosca_vnf to sol6 VNFD
        Currently only handles converting a single VNF to VNFD
        """
        return None

    def convert_variables(self):
        """
        Find the 'get_input' values in the YAML.
        If there is a definition in the TOSCA config file for that given variable name,
        then replace the instances of that variable with the value in the config
        """
        # Also skip the section if the whole section isn't defined
        if "input_values" not in self.variables["tosca"]:
            return

        defined_vars = self.variables["tosca"]["input_values"]
        # If there are no variables defined in the config file, don't bother doing anything
        if not defined_vars:
            return

        inputs = get_roots_from_filter(self.tosca_vnf, child_value="get_input")

        for i in inputs:
            # Strip the outer key, we don't need it
            cur = i[get_dict_key(i)]

            # Now there *should* be at least one {'get_input': ...} under one of the keys in here
            # Try to find that value
            for k in cur.keys():
                # We need the dict so we can modify it via 'reference'
                if k != 'get_input':
                    v = cur[k]
                else:
                    v = cur
                # We know we're looking for a dict, so skip if it isn't one
                if not isinstance(v, dict):
                    continue

                if 'get_input' in v:
                    var_name = v['get_input']
                    # Skip if the given variable isn't one that's defined
                    if var_name not in defined_vars:
                        continue

                    # Overwrite the get_input dict with just the value from the config
                    if k == 'get_input':
                        # We need to overwrite the value of one level above
                        i[get_dict_key(i)] = defined_vars[var_name]
                    else:
                        cur[k] = defined_vars[var_name]

    # *************************
    # ** Run Mapping Methods **
    # *************************
    def run_mapping(self, keys):
        """
        The first parameter is always a tuple, with the flags as the second parameter
        If there are multiple flags, they will be grouped in a tuple as well
        """
        for ((tosca_path, flags), map_sol6) in keys.mapping:
            self.run_mapping_flags(flags, keys)
            self.run_mapping_map_needed(tosca_path, map_sol6)

    def run_mapping_islist(self, tosca_path, map_sol6):
        """
        What to do if there is a complex mapping needed
        Called from run_mapping_map_needed
        """
        mapping_list = map_sol6[1]  # List of MapElems
        sol6_path = map_sol6[0]
        i = -1

        for elem in mapping_list:
            i = i + 1
            # Skip this mapping element if it is None, but allow a none name to pass
            if not elem:
                continue
            if not elem.parent_map and self.req_parent:
                if not self.fail_silent:
                    log.warning("Parent mapping is required, but {} does not have one".format(elem))
                continue

            tosca_use_value = self.tosca_use_value
            f_tosca_path = MapElem.format_path(elem, tosca_path, use_value=tosca_use_value)
            f_sol6_path = MapElem.format_path(elem, sol6_path, use_value=True)

            log.debug("Formatted paths:\n\ttosca: {} --> sol6: {}"
                      .format(f_tosca_path, f_sol6_path))

            # Handle flags for mapped values
            value = self.handle_flags(f_sol6_path, f_tosca_path, i)

            # If the value doesn't exist, don't write it
            # Do write it if the value is 0, though
            write = True
            if not value:
                write = True if value is 0 else False

            if write:
                set_path_to(f_sol6_path, self.vnfd, value, create_missing=True)

    def run_mapping_notlist(self, tosca_path, map_sol6):
        """
        What to do if there is no complex mapping specified
        Called from run_mapping_map_needed
        """
        sol6_path = map_sol6
        if sol6_path is None:
            log.debug("SOL6 path is None, skipping with no error message")
            return

        # Handle the various flags for no mappings
        value = self.handle_flags(sol6_path, tosca_path, 0)

        set_path_to(sol6_path, self.vnfd, value, create_missing=True)

    def run_mapping_map_needed(self, tosca_path, map_sol6):
        """
        Determine if a mapping (list of MapElem) has been specified
        Called by run_mapping
        """
        if tosca_path is None:
            log.debug("Tosca path is None, skipping with no error message")
            return

        log.debug("Run mapping for tosca: {} --> sol6: {}"
                  .format(tosca_path, map_sol6 if not isinstance(map_sol6, list) else map_sol6[0]))

        # Check if there is a mapping needed
        if isinstance(map_sol6, list):
            log.debug("\tMapping: {}".format(map_sol6[1]))
            self.run_mapping_islist(tosca_path, map_sol6)
        else:  # No mapping needed
            self.run_mapping_notlist(tosca_path, map_sol6)

    def run_mapping_flags(self, flags, keys):
        """
        Handle various flag operations, such as setting them to false and updating their values
        Called from run_mapping
        """
        self.set_flags_false()
        self.set_flags_loop(flags, keys)

    # ******************
    # ** Flag methods **
    # ******************
    def handle_flags(self, f_sol6_path, f_tosca_path, run):
        """
        Returns the value after being formatted by the flags
        """

        value = self._key_as_value(self.key_as_value, f_tosca_path)

        value = self._convert_units(self.unit_gb, "GB", value, is_float=self.unit_fractional)
        value = self._only_number(self.only_number, value, is_float=self.only_number_float)
        value = self._min_1(self.min_1, value)
        value = self._append_to_list(self.append_list, f_sol6_path, value)
        value = self._format_as_valid(self.format_as_ip, f_sol6_path, value,
                                      self.variables["sol6"]["VALID_PROTOCOLS_VAL"],
                                      none_found=self.format_invalid_none,
                                      prefix=self.variables["sol6"]["PROTOCOLS_PREFIX_VAL"])
        value = self._format_as_valid(self.format_as_disk, f_sol6_path, value,
                                      self.variables["sol6"]["VALID_DISK_FORMATS_VAL"],
                                      none_found=self.format_invalid_none)
        value = self._format_as_valid(self.format_as_container, f_sol6_path, value,
                                      self.variables["sol6"]["VALID_CONTAINER_FORMATS_VAL"],
                                      none_found=self.format_invalid_none)
        value = self._format_as_valid(self.format_as_aff_scope, f_sol6_path, value,
                                      self.variables["sol6"]["VALID_AFF_SCOPES_VAL"],
                                      none_found=self.format_invalid_none)
        value = self._format_as_valid(self.format_as_storage, f_sol6_path, value,
                                      self.variables["sol6"]["VALID_STORAGE_TYPES_VAL"],
                                      none_found=self.format_invalid_none, fuzzy=True)
        value = self._first_list_elem(self.first_list_elem, f_sol6_path, value)
        value = self._nth_list_elem(self.nth_list_elem, value, run)
        value = self._check_for_null(value)

        return value

    def set_flags_false(self):
        """
        Set all the given flags false.
        If more flags need to be added, override this method
        """
        # Reset these for every mapping
        self.key_as_value       = False
        self.only_number        = False
        self.only_number_float  = False
        self.append_list        = False
        self.first_list_elem    = False
        self.tosca_use_value    = False
        self.format_as_ip       = False
        self.format_as_container = False
        self.format_as_disk     = False
        self.format_as_aff_scope = False
        self.format_as_storage = False
        self.fail_silent        = False
        self.req_parent         = False
        self.format_invalid_none = False
        self.unit_gb            = False
        self.unit_fractional    = False
        self.min_1              = False

    def set_flags_loop(self, flags, keys):
        """
        Handle figuring out which flags need to be set in O(n) time
        """
        # Ensure flags is iterable
        if not isinstance(flags, tuple):
            flags = [flags]
        if flags and not flags[0] == '':
            log.debug("Flags: {}".format(flags))

        for flag in flags:
            if flag == keys.FLAG_KEY_SET_VALUE:
                self.key_as_value = True
            if flag == keys.FLAG_ONLY_NUMBERS:
                self.only_number = True
            if flag == keys.FLAG_APPEND_LIST:
                self.append_list = True
            if flag == keys.FLAG_ONLY_NUMBERS_FLOAT:
                self.only_number_float = True
            if flag == keys.FLAG_LIST_FIRST:
                self.first_list_elem = True
            if flag == keys.FLAG_LIST_NTH:
                self.nth_list_elem = True
            if flag == keys.FLAG_USE_VALUE:
                self.tosca_use_value = True
            if flag == keys.FLAG_FORMAT_IP:
                self.format_as_ip = True
            if flag == keys.FLAG_FAIL_SILENT:
                self.fail_silent = True
            if flag == keys.FLAG_REQ_PARENT:
                self.req_parent = True
            if flag == keys.FLAG_FORMAT_DISK_FMT:
                self.format_as_disk = True
            if flag == keys.FLAG_FORMAT_CONT_FMT:
                self.format_as_container = True
            if flag == keys.FLAG_FORMAT_AFF_SCOPE:
                self.format_as_aff_scope = True
            if flag == keys.FLAG_FORMAT_STORAGE_TYPE:
                self.format_as_storage = True
            if flag == keys.FLAG_FORMAT_INVALID_NONE:
                self.format_invalid_none = True
            if flag == keys.FLAG_UNIT_GB:
                self.unit_gb = True
            if flag == keys.FLAG_UNIT_FRACTIONAL:
                self.unit_fractional = True
            if flag == keys.FLAG_MIN_1:
                self.min_1 = True

    # ---------------------
    # ** Specific flag methods **
    def _append_to_list(self, option, path, value):
        if not option:
            return value
        cur_list = get_path_value(path, self.vnfd, must_exist=False, no_msg=self.fail_silent)
        # If it doesn't exist, create it
        if not cur_list:
            cur_list = []

        # This means a value exists in the path, so convert it to a list
        if not isinstance(cur_list, list):
            # Convert it to a list, then continue
            cur_list = [cur_list]

        # Now that everything is together in a list, append the value
        cur_list.append(value)
        return cur_list

    def _key_as_value(self, option, path):
        if option:
            return KeyUtils.get_path_last(path)
        return get_path_value(path, self.tosca_vnf, must_exist=False, no_msg=self.fail_silent)

    @staticmethod
    def _only_number(option, value, is_float=False):
        if not option:
            return value
        cur_type = int
        if is_float:
            cur_type = float
        if not isinstance(value, str):
            return value
        return cur_type(re.sub('[^0-9]', '', str(value)))

    @staticmethod
    def _min_1(option, value):
        if not option:
            return value
        return value if value > 1 else 1

    @staticmethod
    def _first_list_elem(option, path, value):
        if not option or not isinstance(value, list):
            return value
        return value[0]

    @staticmethod
    def _nth_list_elem(option, value, n):
        if not option or not isinstance(value, list):
            return value
        if len(value) > n:
            return value[n]
        else:
            return value[-1]

    @classmethod
    def _format_as_valid(cls, option, path, value, valid_formats, none_found=False, prefix="", fuzzy=False):
        """
        Take the value, and a list of valid options, see if the value is any of the valid ones.
        Return the output as a list (for some reason)
        :optional none_found: Return None if a valid match is not found
        """
        if not option:
            return value
        # Turn it into a list if it isn't already
        if not isinstance(value, list):
            value = [value]
        else:
            # If it is, make sure it isn't a reference to the tosca_vnf
            value = list(value)
        for i, item in enumerate(value):
            found, value[i] = cls._fmt_val(item, valid_formats, none_found, fuzzy=fuzzy)
            if not found:
                log.error("Value '{}' not found in valid formats: {}".format(item, valid_formats))
            if value[i]:
                value[i] = prefix + value[i]
        # Any value not matching will be returned with a (INVALID) at the end
        return value

    @staticmethod
    def _fmt_val(val, valid_opts, return_none, fuzzy=False):
        """Format the value with the list, called from _format_as_valid"""
        if not isinstance(val, str):
            return False, "{} (INVALID)".format(val)

        tmp_val = val.lower()

        for opt in valid_opts:
            tmp_opt = opt.lower()
            tmp_val = tmp_val.replace("_", "-")
            # We found a valid mapping, so set the value to the actual formatted value
            if tmp_val == tmp_opt:
                return True, str(opt)
            # Do more lax checking if specified
            if fuzzy:
                if tmp_val in tmp_opt or tmp_opt in tmp_val:
                    return True, str(opt)

        if return_none:
            return False, None
        return False, "{} (INVALID)".format(val)

    @staticmethod
    def _check_for_null(value):
        if value == "[null]":
            return [None]
        return value

    @staticmethod
    def _convert_units(opt, unit, value, decimal_places=1, is_float=False):
        """
        Attempt to figure out what the unit is, and convert to the given one
        Currently the only supported output unit is
        """
        if not opt:
            return value
        if not value:
            return value

        valid_units = ["GB"]  # Make sure these are in all caps
        if unit.upper() not in valid_units:
            raise KeyError("Unknown unit, valid units: {}".format(valid_units))

        # If the result can't be fractional, rounding to 0 decimal places doesn't work
        value_num = Sol6Converter._only_number(True, value, is_float=is_float)
        try:
            if "mb" in value.lower():
                if is_float:
                    value_num = round(value_num / 1024, decimal_places)
                else:
                    value_num = value_num // 1024

        except AttributeError as e:
            if "lower" in str(e):
                raise AttributeError("'int' object '{}' has no attribute 'lower'. Ensure the value has a UNIT"
                                     .format(value)) from e
            else:
                raise e

        return value_num

    # ---------------------

    @staticmethod
    def find_provider(tosca_lines):
        """
        Do a dumb search over the file to find the provider
        """
        found = None
        for l in tosca_lines:
            if "provider:" in str(l):
                found = l
                break
        if not found:
            raise ValueError("Provider not found")
        prov = found.decode("utf-8").strip()
        val = prov.split(":")[-1].strip()
        return val.lower()


def is_hashable(obj):
    """Determine whether 'obj' can be hashed."""
    try:
        hash(obj)
    except TypeError:
        return False
    return True
