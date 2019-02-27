import re
from sol6_keys_cisco import *
from sol6_converter import Sol6Converter
from dict_utils import *
import copy


class SOL6ConverterCisco(Sol6Converter):

    def __init__(self, tosca_vnf, parsed_dict, variables=None, log=None):
        super().__init__(tosca_vnf, parsed_dict, variables, log)

    def parse(self):
        """
        Convert the tosca_vnf to sol6 VNFD
        Currently only handles converting a single VNF to VNFD
        """
        self.log.info("Starting Cisco TOSCA -> SOL6 (v{}) converter.".format(self.SUPPORTED_SOL6_VERSION))

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
