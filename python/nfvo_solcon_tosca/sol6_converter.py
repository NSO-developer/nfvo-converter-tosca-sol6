"""

"""
import re
from sol6_keys import *
from dict_utils import *
import copy
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
        self.flavor_names = []
        self.connection_points = {}
        self.tosca_vdus = {}
        self.flavor_vars = {}
        self.run_deltas = True
        # If we want to hard skip the loop that runs the deltas
        self.override_run_deltas = False

        # Set up the flag variables
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

    def parse(self):
        """
        Convert the tosca_vnf to sol6 VNFD
        Currently only handles converting a single VNF to VNFD
        """
        # TODO: Handle multiple vnfds
        self.log.info("Starting TOSCA -> SOL6 (v{}) converter.".format(self.SUPPORTED_SOL6_VERSION))
        raise TypeError("Unsupported provider")

        # The very first thing we want to do is set up the path variables
        self.log.debug("Setting path variables: {}".format(self.variables))
        TOSCA.set_variables(self.variables, self.tosca_vnf)
        SOL6.set_variables(self.variables)

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

        self.run_v2_mapping(keys)

        return self.vnfd

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

