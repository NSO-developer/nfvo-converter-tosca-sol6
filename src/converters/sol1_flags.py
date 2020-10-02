from converters.sol6_converter import Sol6Converter
from mapping_v2 import *
import re
from utils.key_utils import KeyUtils


class Sol1Flags:
    def __init__(self,  sol1_vnfd, sol6_vnfd):
        self.sol6_vnfd = sol6_vnfd
        self.sol1_vnfd = sol1_vnfd

        # Set up the flag variables
        # We probably won't need all of these for SOL1
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

    # ******************
    # ** Flag methods **
    # ******************
    def handle_flags(self, f_sol6_path, f_sol1_path, run):
        """
        Returns the value after being formatted by the flags
        """

        value = self._key_as_value(self.key_as_value, f_sol6_path)
        value = self._convert_units(self.unit_gb, "GB", value, is_float=self.unit_fractional)
        value = self._only_number(self.only_number, value, is_float=self.only_number_float)
        value = self._min_1(self.min_1, value)
        value = self._append_to_list(self.append_list, f_sol1_path, value)
        # value = self._format_as_valid(self.format_as_ip, f_sol6_path, value,
        #                               self.variables["sol6"]["VALID_PROTOCOLS_VAL"],
        #                               none_found=self.format_invalid_none,
        #                               prefix=self.variables["sol6"]["PROTOCOLS_PREFIX_VAL"])
        # value = self._format_as_valid(self.format_as_disk, f_sol6_path, value,
        #                               self.variables["sol6"]["VALID_DISK_FORMATS_VAL"],
        #                               none_found=self.format_invalid_none)
        # value = self._format_as_valid(self.format_as_container, f_sol6_path, value,
        #                               self.variables["sol6"]["VALID_CONTAINER_FORMATS_VAL"],
        #                               none_found=self.format_invalid_none)
        # value = self._format_as_valid(self.format_as_aff_scope, f_sol6_path, value,
        #                               self.variables["sol6"]["VALID_AFF_SCOPES_VAL"],
        #                               none_found=self.format_invalid_none)
        # value = self._format_as_valid(self.format_as_storage, f_sol6_path, value,
        #                               self.variables["sol6"]["VALID_STORAGE_TYPES_VAL"],
        #                               none_found=self.format_invalid_none, fuzzy=True)
        value = self._first_list_elem(self.first_list_elem, value)
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
        self.nth_list_elem      = False
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
        cur_list = get_path_value(path, self.sol1_vnfd, must_exist=False, no_msg=self.fail_silent)
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
        return get_path_value(path, self.sol6_vnfd, must_exist=False, no_msg=self.fail_silent)

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
    def _first_list_elem(option, value):
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

    @classmethod
    def _convert_units(cls, opt, unit, value, decimal_places=1, is_float=False):
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
        value_num = cls._only_number(True, value, is_float=is_float)
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
