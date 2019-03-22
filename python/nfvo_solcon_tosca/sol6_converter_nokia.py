from sol6_keys_nokia import *
from sol6_converter import Sol6Converter


class SOL6ConverterNokia(Sol6Converter):

    def __init__(self, tosca_vnf, parsed_dict, variables=None):
        super().__init__(tosca_vnf, parsed_dict, variables=variables)

    def convert(self, provider=None):
        """
        Convert the tosca_vnf to sol6 VNFD
        Currently only handles converting a single VNF to VNFD
        """
        log.info("Starting Nokia TOSCA -> SOL6 converter.")
        
        self.vnfd = {}
        formatted_vars = PathMaping.format_paths(self.variables)
        TOSCA.set_variables(self.variables["tosca"], TOSCA, "identifiers", variables=formatted_vars,
                            dict_tosca=self.tosca_vnf, cur_provider=provider)

        keys = V2Map(self.tosca_vnf, self.vnfd, variables=self.variables)

        self.run_mapping(keys)

        return self.vnfd
