from sol6_keys import *


class TOSCA(TOSCA_BASE):

    topology_template                   = ""
    substitution_mappings               = ""
    descriptor_id                       = ""
    descriptor_version                  = ""
    provider                            = ""
    product_name                        = ""
    product_info_name                   = ""
    product_info_desc                   = ""
    software_version                    = ""
    vnfm_info                           = ""
    requirements                        = ""

    vnf                                 = ""
    vnf_provider                        = ""

    virtual_compute_identifier          = []

    @staticmethod
    def set_variables(cur_dict, obj, exclude="", variables=None, dict_tosca=None):
        """
        Take the input from the config file, and set the variables that are identifiers here
        This must be run before the values are used
        """
        TOSCA_BASE.set_variables(cur_dict, obj, exclude="identifier")

        cur_provider = get_path_value(TOSCA.vnf_provider, dict_tosca).lower()
        possible_providers = variables['providers']
        
        # We must have a provider mapping
        if cur_provider not in possible_providers:
            raise KeyError("Provider {} not found in possible providers {}"
                           .format(cur_provider, possible_providers))

        provider_identifiers = variables["provider-identifiers"][cur_provider]

        # Load the basic identifiers
        vdu_identifier = provider_identifiers["vdu"]
        int_cpd_identifier = provider_identifiers["int-cpd"]
        inst_level_identifier = provider_identifiers["instantiation-level"]
        scaling_aspects_identifier = provider_identifiers["scaling-aspects"]
        virt_storage_identifier = provider_identifiers["virtual-storage"]
        int_cpd_mgmt_identifier = provider_identifiers["int-cpd-mgmt"]

        # Add the filter functions to the relevant identifiers
        virt_storage_identifier.append(TOSCA.virt_filter)
        int_cpd_mgmt_identifier.append(TOSCA.int_cp_mgmt)

        # Assign the read values
        TOSCA.vdu_identifier = vdu_identifier
        TOSCA.int_cpd_identifier = int_cpd_identifier
        TOSCA.int_cpd_mgmt_identifier = int_cpd_mgmt_identifier
        TOSCA.inst_level_identifier = inst_level_identifier
        TOSCA.scaling_aspects_identifier = scaling_aspects_identifier
        TOSCA.virt_storage_identifier = virt_storage_identifier


class SOL6(SOL6_BASE):
    pass


class V2Map(V2Map):
    def __init__(self, dict_tosca, dict_sol6, variables=None, log=None):
        super().__init__(dict_tosca, dict_sol6, log=log)
        T = TOSCA
        S = SOL6

        # Virtual compute & storage mapping
        virt_comp = get_roots_from_filter(dict_tosca, child_key=T.virtual_compute_identifier[0],
                                          child_value=T.virtual_compute_identifier[1])

        self.mapping = [
            # ** Metadata **
            ((T.descriptor_id, self.FLAG_BLANK),        S.vnfd_id),
            ((T.descriptor_version, self.FLAG_BLANK),   S.vnfd_ver),
            ((T.provider, self.FLAG_BLANK),             S.vnfd_provider),
            ((T.product_name, self.FLAG_BLANK),         S.vnfd_product),
            ((T.product_info_name, self.FLAG_BLANK),    S.vnfd_info_name),
            ((T.product_info_desc, self.FLAG_BLANK),    S.vnfd_info_desc),
            ((T.software_version, self.FLAG_BLANK),     S.vnfd_software_ver),
            ((T.vnfm_info, self.FLAG_BLANK),            S.vnfd_vnfm_info)


        ]


