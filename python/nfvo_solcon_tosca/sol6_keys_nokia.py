from sol6_keys import *


class TOSCA(TOSCA):

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


class SOL6(SOL6):
    pass


class V2Map(V2Map):
    def __init__(self, dict_tosca, dict_sol6, variables=None, log=None):
        super().__init__(dict_tosca, dict_sol6, log=log)

        self.log.debug("Setting path variables: {}".format(variables))

        TOSCA.set_variables(variables, dict_tosca, TOSCA)
        # SOL6.set_variables(self.variables)

        print(TOSCA.software_version, get_path_value(TOSCA.software_version, dict_tosca))



