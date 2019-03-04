import re
from sol6_keys_cisco import *
from sol6_converter import Sol6Converter
from dict_utils import *
import copy


class SOL6ConverterCisco(Sol6Converter):

    def __init__(self, tosca_vnf, parsed_dict, variables=None, log=None):
        super().__init__(tosca_vnf, parsed_dict, variables, log)

        # Initialize the flag variables you use here, even though they'll always be defined
        # by set_flags_false, it's good practice
        self.req_delta_valid = False
        self.format_as_ip = False
        self.is_variable = False
        self.default_root = False

    def convert(self):
        """
        Convert the tosca_vnf to sol6 VNFD
        Currently only handles converting a single VNF to VNFD
        """
        self.log.info("Starting Cisco TOSCA -> SOL6 (v{}) converter.".format(self.SUPPORTED_SOL6_VERSION))

        # The very first thing we want to do is set up the path variables
        self.log.debug("Setting path variables: {}".format(self.variables))
        TOSCA.set_variables(self.variables["tosca"], TOSCA, variables=self.variables,
                            dict_tosca=self.tosca_vnf)
        SOL6.set_variables(self.variables["sol6"], SOL6)

        # First, get the vnfd specifications model
        try:
            self.vnfd = copy.deepcopy(self.parsed_dict[SOL6.vnfd])
        except KeyError:
            self.vnfd = {}

        keys = V2Map(self.tosca_vnf, self.vnfd, self.log)
        if keys.override_deltas:
            self.override_run_deltas = not keys.run_deltas
        else:
            self.check_deltas_valid()

        self.run_mapping(keys)

        return self.vnfd

    def run_mapping(self, keys):
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
            if flag == keys.FLAG_FORMAT_IP:
                self.format_as_ip = True

    def handle_flags(self, f_sol6_path, f_tosca_path):
        value = super().handle_flags(f_sol6_path, f_tosca_path)
        value = self._handle_input(self.is_variable, f_sol6_path, value)
        value = self._handle_default_root(self.default_root, f_sol6_path, value)
        value = self._format_as_ip(self.format_as_ip, f_sol6_path, value)

        return value

    # Flag option formatting methods
    @staticmethod
    def _handle_default_root(option, path, value):
        if not option:
            return value
        if not value:
            return SOL6.VIRT_STORAGE_DEFAULT
        return value

    @staticmethod
    def _handle_input(option, path, value):
        if not option:
            return value
        # See if this is actually an input, if can not be
        is_input = V2Mapping.is_tosca_input(value)
        # If this isn't actually an input, then don't assign it
        if not is_input:
            return None
        return V2Mapping.tosca_get_input_key(value)

    @staticmethod
    def _format_as_ip(option, path, value):
        if not option:
            return value
        valid_opts = SOL6.VALID_PROTOCOLS

        def _fmt_val(val):
            for opt in valid_opts:
                # We found a valid mapping, so set the value to the actual formatted value
                if val.lower() == opt.lower():
                    return opt
        # Turn it into a list if it isn't already
        if not isinstance(value, list):
            value = [value]

        for i, item in enumerate(value):
            value[i] = _fmt_val(item)
        # If we don't find a matching value, pass the original value through so it's not lost
        return value

    # ----------------------------------------------------------------------------------------------

    def check_deltas_valid(self):
        """
        We are only supporting step_deltas that have unique names across the entire yaml file
        I don't care that YAML supports more.
        """
        step_deltas_name = KeyUtils.get_path_last(TOSCA.scaling_aspect_deltas)
        # Get all the elements that have step_deltas
        deltas = get_roots_from_filter(self.tosca_vnf, child_key=step_deltas_name)
        # Get all the values of 'step_deltas' and stick them in a list
        try:
            all_deltas = [delta[get_dict_key(delta)][step_deltas_name] for delta in deltas]
            all_deltas = flatten(all_deltas)
        except KeyError:
            # We're going to assume that if we can't do the check to just try to run deltas
            return

        # Determine if there are any duplicates
        if len(all_deltas) != len(set(all_deltas)):
            self.log.warning("step_deltas were detected that have the same name, "
                             "this is not suppported and thus deltas will not be processed.")
            self.run_deltas = False
