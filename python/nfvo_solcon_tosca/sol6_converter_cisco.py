import re
from sol6_keys_cisco import *
from sol6_converter import Sol6Converter
from sol6_keys import *
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

    def convert(self, provider=None):
        """
        Convert the tosca_vnf to sol6 VNFD
        Currently only handles converting a single VNF to VNFD
        """
        self.log.info("Starting Cisco TOSCA -> SOL6 (v{}) converter.".format(self.SUPPORTED_SOL6_VERSION))

        # The very first thing we want to do is set up the path variables
        self.log.debug("Setting path variables: {}".format(self.variables))
        formatted_vars = PathMaping.format_paths(self.variables)

        TOSCA.set_variables(self.variables["tosca"], TOSCA, variables=formatted_vars,
                            dict_tosca=self.tosca_vnf, cur_provider=provider)

        self.vnfd = {}

        keys = V2Map(self.tosca_vnf, self.vnfd, log=self.log, variables=self.variables)
        if keys.override_deltas:
            self.override_run_deltas = not keys.run_deltas
        else:
            self.check_deltas_valid(keys.get_tosca_value("scaling_aspect_deltas"))

        self.run_mapping(keys)

        return self.vnfd

    def run_mapping_islist(self, tosca_path, map_sol6):
        mapping_list = map_sol6[1]  # List of MapElems
        sol6_path = map_sol6[0]

        if self.override_run_deltas:
            # Skip this iteration if needed
            if self.req_delta_valid and not mapping_list:
                return

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

    def handle_flags(self, f_sol6_path, f_tosca_path):
        value = super().handle_flags(f_sol6_path, f_tosca_path)
        value = self._handle_input(self.is_variable, f_sol6_path, value)
        value = self._handle_default_root(self.default_root, f_sol6_path, value)

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
        is_input = V2MapBase.is_tosca_input(value)
        # If this isn't actually an input, then don't assign it
        if not is_input:
            return None
        return V2MapBase.tosca_get_input_key(value)

    # ----------------------------------------------------------------------------------------------

    def check_deltas_valid(self, scaling_aspect):
        """
        We are only supporting step_deltas that have unique names across the entire yaml file
        I don't care that YAML supports more.
        """
        step_deltas_name = KeyUtils.get_path_last(scaling_aspect)
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
