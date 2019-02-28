from sol6_keys_nokia import *
from sol6_converter import Sol6Converter
import copy


class SOL6ConverterNokia(Sol6Converter):

    def __init__(self, tosca_vnf, parsed_dict, variables=None, log=None):
        super().__init__(tosca_vnf, parsed_dict, variables=variables, log=log)

    def parse(self):
        """
        Convert the tosca_vnf to sol6 VNFD
        Currently only handles converting a single VNF to VNFD
        """
        self.log.info("Starting Nokia TOSCA -> SOL6 (v{}) converter.".format(self.SUPPORTED_SOL6_VERSION))

        self.vnfd = {}
        TOSCA.set_variables(self.variables["tosca"], TOSCA, "identifiers")
        SOL6.set_variables(self.variables["sol6"], SOL6)

        keys = V2Map(self.tosca_vnf, self.vnfd, variables=self.variables, log=self.log)

        #self.run_v2_mapping(keys)

        return self.vnfd
