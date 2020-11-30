from keys.sol6_keys_cisco import *
from converters.sol6_converter import Sol6Converter
from keys.sol6_keys import *
from utils.dict_utils import *


class SOL6ConverterCisco(Sol6Converter):

    def __init__(self, tosca_vnf, parsed_dict, variables=None):
        super().__init__(tosca_vnf, parsed_dict, variables)

        # Initialize the flag variables you use here, even though they'll always be defined
        # by set_flags_false, it's good practice
        self.req_delta_valid = False
        self.format_as_ip = False
        self.is_variable = False
        self.default_root = False

    def convert(self, provider=None):
        """
        Convert the tosca_vnf to sol6 VNFD
        Currently only handles converting a single VNF to VNFD
        """
        log.info("Starting Cisco TOSCA -> SOL6 converter.")

        # The very first thing we want to do is set up the path variables
        log.debug("Setting path variables: {}".format(self.variables))
        formatted_vars = PathMapping.format_paths(self.variables)

        TOSCA.set_variables(self.variables["tosca"], TOSCA, variables=formatted_vars,
                            dict_tosca=self.tosca_vnf, cur_provider=provider)

        self.vnfd = {}

        keys = V2Map(self.tosca_vnf, self.vnfd, variables=self.variables)

        self.run_mapping(keys)

        return self.vnfd

    def run_mapping_islist(self, tosca_path, map_sol6):
        mapping_list = map_sol6[1]  # List of MapElems
        sol6_path = map_sol6[0]
        i = -1
        for elem in mapping_list:
            i = i + 1
            # Skip this mapping element if it is None, but allow a none name to pass
            if not elem:
                continue

            tosca_use_value = self.tosca_use_value
            f_tosca_path = MapElem.format_path(elem, tosca_path, use_value=tosca_use_value)
            f_sol6_path = MapElem.format_path(elem, sol6_path, use_value=True)
            log.debug("Formatted paths:\n\ttosca: {} --> sol6: {}"
                      .format(f_tosca_path, f_sol6_path))

            # Skip this element if it requires deltas to be valid
            # This has to be outside the flag method
            if self.req_delta_valid:
                if not self.run_deltas:
                    continue

            # Handle flags for mapped values
            value = self.handle_flags(f_sol6_path, f_tosca_path, i)

            # If the value doesn't exist, don't write it
            # Do write it if the value is 0, though
            write = True
            if not value:
                write = True if value is 0 else False

            if write:
                set_path_to(f_sol6_path, self.vnfd, value, create_missing=True)

    def set_flags_false(self):
        """
        Set all the flags defined in this class to false.
        This resets them every loop so they aren't applied when they shouldn't be.
        """
        super().set_flags_false()
        self.is_variable = False
        self.default_root = False
        self.req_delta_valid = False
        self.format_as_ip = False

    def set_flags_loop(self, flags, keys):
        super().set_flags_loop(flags, keys)
        # Ensure flags is iterable
        if not isinstance(flags, tuple):
            flags = [flags]

        for flag in flags:
            if flag == keys.FLAG_VAR:
                self.is_variable = True
            if flag == keys.FLAG_TYPE_ROOT_DEF:
                self.default_root = True
            if flag == keys.FLAG_REQ_DELTA:
                self.req_delta_valid = True

    def handle_flags(self, f_sol6_path, f_tosca_path, run):
        value = super().handle_flags(f_sol6_path, f_tosca_path, run)
        value = self._handle_input(self.is_variable, f_sol6_path, value)
        value = self._handle_default_root(self.default_root, f_sol6_path, value)

        return value

    # Flag option formatting methods
    def _handle_default_root(self, option, path, value):
        if not option:
            return value
        if not value:
            return self.variables["sol6"]["VIRT_STORAGE_DEFAULT_VAL"]
        return value

    @staticmethod
    def _handle_input(option, path, value):
        if not option:
            return value

        # If this isn't actually an input, then don't assign it
        if not V2MapBase.is_tosca_input(value):
            return value

        return V2MapBase.tosca_get_input_key(value)

    # ----------------------------------------------------------------------------------------------
