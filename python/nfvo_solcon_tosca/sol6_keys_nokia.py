from sol6_keys import *


class TOSCA(TOSCA_BASE):

    topology_template = ""
    substitution_mappings = ""
    descriptor_id = ""
    descriptor_version = ""
    provider = ""
    product_name = ""
    software_version = ""
    vnfm_info = ""
    requirements = ""

    vnf = ""


class SOL6(SOL6_BASE):
    pass


class V2Map(V2Map):
    def __init__(self, dict_tosca, dict_sol6, variables=None, log=None):
        super().__init__(dict_tosca, dict_sol6, log=log)

        self.mapping = [

        ]



