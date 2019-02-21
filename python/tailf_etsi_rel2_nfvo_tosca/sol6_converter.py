"""

"""
import re
from sol6_keys import *
from dict_utils import *


class Sol6Converter:
    SUPPORTED_SOL6_VERSION = "1.1"

    tosca_vnf = None
    parsed_dict = None
    vnfd = None
    template_inputs = {}
    log = None
    keys = None

    def __init__(self, tosca_vnf, parsed_dict, log=None):
        self.tosca_vnf = tosca_vnf
        self.parsed_dict = parsed_dict
        self.log = log
        # Set this up for _virtual_get_flavor_names
        self.flavor_names = []
        self.connection_points = {}
        self.tosca_vdus = {}
        self.flavor_vars = {}
        self.run_deltas = True

    def parse(self):
        """
        Convert the tosca_vnf to sol6 VNFD
        Currently only handles converting a single VNF to VNFD
        """
        # TODO: Handle multiple vnfds
        print("Starting TOSCA -> SOL6 (v{}) converter.".format(self.SUPPORTED_SOL6_VERSION))
        # First, get the vnfd specifications model
        self.vnfd = copy.deepcopy(self.parsed_dict[SOL6v2.vnfd])

        keys = V2Map(self.tosca_vnf, self.vnfd)
        self.check_deltas_valid()

        self.run_v2_mapping(keys)

        # Get all of the inputs from tosca
        #self.template_inputs = get_path_value(TOSCA.inputs, self.tosca_vnf)

        #self._handle_virtual_compute()
        #self._handle_virtual_link()

        return self.vnfd

    def run_v2_mapping(self, keys):
        # The first parameter is always a tuple, with the flags as the second parameter
        # If there are multiple flags, they will be grouped in a tuple as well

        for ((tosca_path, flags), map_sol6) in keys.mapping:
            key_as_value = False
            only_number = False
            only_number_float = False
            append_list = False
            req_delta_valid = False
            init_dict = False

            # Ensure flags is iterable
            if not isinstance(flags, tuple):
                flags = [flags]
            for flag in flags:
                if flag == keys.FLAG_KEY_SET_VALUE:
                    key_as_value = True
                if flag == keys.FLAG_ONLY_NUMBERS:
                    only_number = True
                if flag == keys.FLAG_APPEND_LIST:
                    append_list = True
                if flag == keys.FLAG_ONLY_NUMBERS_FLOAT:
                    only_number_float = True
                if flag == keys.FLAG_REQ_DELTA:
                    req_delta_valid = True

            # Check if there is a mapping needed
            if isinstance(map_sol6, list):
                mapping_list = map_sol6[1]  # List of MapElems
                sol6_path = map_sol6[0]

                for elem in mapping_list:
                    # Skip this mapping element if it is None or it's name is none
                    if not elem or not elem.name:
                        continue

                    f_tosca_path = MapElem.format_path(elem, tosca_path, use_value=False)
                    f_sol6_path = MapElem.format_path(elem, sol6_path, use_value=True)

                    # Handle the various flags
                    # Skip this element if it requires deltas to be valid
                    if req_delta_valid:
                        if not self.run_deltas:
                            continue

                    value = self._key_as_value(key_as_value, f_tosca_path)
                    value = Sol6Converter._only_number(only_number, value,
                                                       is_float=only_number_float)
                    value = self._append_to_list(append_list, f_sol6_path, value)

                    # If the value doesn't exist, don't write it
                    # Do write it if the value is 0, though
                    write = True
                    if not value:
                        write = True if value is 0 else False

                    if write:
                        set_path_to(f_sol6_path, self.vnfd, value, create_missing=True)
            else:  # No mapping needed
                sol6_path = map_sol6

                # Handle the various flags
                value = self._key_as_value(key_as_value, tosca_path)
                value = Sol6Converter._only_number(only_number, value, is_float=only_number_float)

                set_path_to(sol6_path, self.vnfd, value, create_missing=True)

    # Flag option formatting methods
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

    # ----------------------------------------------------------------------------------------------

    def check_deltas_valid(self):
        """
        We are only supporting step_deltas that have unique names across the entire yaml file
        I don't care that YAML supports more.
        """
        step_deltas_name = KeyUtils.get_path_last(TOSCAv2.scaling_aspect_deltas)
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
            print("WARNING: step_deltas were detected that have the same name, "
                  "this is not suppported and thus deltas will not be processed.")
            self.run_deltas = False

# ******* Static Methods ********


def get_object_keys(obj):
    return [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and
            not (attr.startswith("__") or attr.startswith("_"))]


def is_hashable(obj):
    """Determine whether 'obj' can be hashed."""
    try:
        hash(obj)
    except TypeError:
        return False
    return True
