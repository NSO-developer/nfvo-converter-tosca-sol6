"""

"""
import re
from sol6_keys import *
from dict_utils import *
import copy
from key_utils import KeyUtils
from functools import wraps


class Sol6Converter:
    SUPPORTED_SOL6_VERSION = "1.1"

    tosca_vnf = None
    parsed_dict = None
    vnfd = None
    template_inputs = {}
    log = None
    keys = None

    def __init__(self, tosca_vnf, parsed_dict, variables=None, log=None):
        self.tosca_vnf = tosca_vnf
        self.parsed_dict = parsed_dict
        self.log = log
        self.variables = variables

        # Set this up for _virtual_get_flavor_names
        self.run_deltas = True
        # If we want to hard skip the loop that runs the deltas
        self.override_run_deltas = False

        # Set up the flag variables
        self.key_as_value = False
        self.only_number = False
        self.only_number_float = False
        self.append_list = False
        self.first_list_elem = False
        self.tosca_use_value = False

    def parse(self):
        """
        For overriding
        Convert the tosca_vnf to sol6 VNFD
        Currently only handles converting a single VNF to VNFD
        """
        return None

    def run_v2_mapping(self, keys):
        # The first parameter is always a tuple, with the flags as the second parameter
        # If there are multiple flags, they will be grouped in a tuple as well

        for ((tosca_path, flags), map_sol6) in keys.mapping:
            self.set_flags_false()
            self.set_flags_loop(flags, keys)

            # Check if there is a mapping needed
            if isinstance(map_sol6, list):
                mapping_list = map_sol6[1]  # List of MapElems
                sol6_path = map_sol6[0]

                if self.override_run_deltas:
                    if self.req_delta_valid and not mapping_list:
                        continue

                for elem in mapping_list:
                    # Skip this mapping element if it is None, but allow a none name to pass
                    if not elem:
                        continue

                    tosca_use_value = self.tosca_use_value
                    f_tosca_path = MapElem.format_path(elem, tosca_path, use_value=tosca_use_value)
                    f_sol6_path = MapElem.format_path(elem, sol6_path, use_value=True)

                    # Skip this element if it requires deltas to be valid
                    # This has to be outside the flag method
                    if self.req_delta_valid:
                        if not self.run_deltas:
                            continue

                    # Handle flags for mapped values
                    value = self.handle_flags(f_sol6_path, f_tosca_path)

                    # If the value doesn't exist, don't write it
                    # Do write it if the value is 0, though
                    write = True
                    if not value:
                        write = True if value is 0 else False

                    if write:
                        set_path_to(f_sol6_path, self.vnfd, value, create_missing=True)
            else:  # No mapping needed
                sol6_path = map_sol6

                # Handle the various flags for no mappings
                value = self.handle_flags(sol6_path, tosca_path)

                set_path_to(sol6_path, self.vnfd, value, create_missing=True)

    # ** Flag methods **

    def set_flags_false(self):
        """
        Set all the given flags false.
        If more flags need to be added, override this method
        """
        # Reset these for every mapping
        self.key_as_value = False
        self.only_number = False
        self.only_number_float = False
        self.append_list = False
        self.req_delta_valid = False
        self.format_as_ip = False
        self.first_list_elem = False
        self.tosca_use_value = False
        self.is_variable = False
        self.default_root = False

    def set_flags_loop(self, flags, keys):
        """
        Handle figuring out which flags need to be set in O(n) time
        """
        # Ensure flags is iterable
        if not isinstance(flags, tuple):
            flags = [flags]
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

    def handle_flags(self, f_sol6_path, f_tosca_path):
        """
        Returns the value after being formatted by the flags
        """
        value = self._key_as_value(self.key_as_value, f_tosca_path)
        value = self._only_number(self.only_number, value, is_float=self.only_number_float)
        value = self._append_to_list(self.append_list, f_sol6_path, value)
        value = self._first_list_elem(self.first_list_elem, f_sol6_path, value)

        return value

    # ---------------------
    # ** Specific flag methods **
    def _append_to_list(self, option, path, value):
        if not option:
            return value
        cur_list = get_path_value(path, self.vnfd, must_exist=False)
        if cur_list:
            if not isinstance(cur_list, list):
                raise TypeError("{} is not a list".format(cur_list))
            cur_list.append(value)

    def _key_as_value(self, option, path):
        if option:
            return KeyUtils.get_path_last(path)
        return get_path_value(path, self.tosca_vnf, must_exist=False)

    @staticmethod
    def _only_number(option, value, is_float=False):
        if not option:
            return value
        cur_type = int
        if is_float:
            cur_type = float
        return cur_type(re.sub('[^0-9]', '', str(value)))

    @staticmethod
    def _first_list_elem(option, path, value):
        if not option or not isinstance(value, list):
            return value
        return value[0]
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

