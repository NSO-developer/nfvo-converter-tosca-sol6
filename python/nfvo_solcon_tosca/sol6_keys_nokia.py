from sol6_keys import *


class TOSCA(TOSCA_BASE):
    virtual_compute_identifier          = []

    @staticmethod
    def set_variables(cur_dict, obj, exclude="", variables=None, dict_tosca=None):
        """
        Take the input from the config file, and set the variables that are identifiers here
        This must be run before the values are used
        """
        cur_provider = get_path_value(variables["tosca"]["vnf_provider"], dict_tosca).lower()
        possible_providers = variables['providers']
        
        # We must have a provider mapping
        if cur_provider not in possible_providers:
            raise KeyError("Provider {} not found in possible providers {}"
                           .format(cur_provider, possible_providers))

        provider_identifiers = variables["provider-identifiers"][cur_provider]

        # Load the basic identifiers
        virt_compute_id = provider_identifiers["virtual-compute"]

        # Assign the read values
        variables["tosca"]["virtual_compute_identifier"] = virt_compute_id


class SOL6(SOL6_BASE):
    pass


class V2Map(V2Map):
    def __init__(self, dict_tosca, dict_sol6, variables=None, log=None):
        super().__init__(dict_tosca, dict_sol6, log=log)
        vaT = variables["tosca"]
        vaS = variables["sol6"]
        S = SOL6

        # Virtual compute & storage mapping
        vci = vaT["virtual_compute_identifier"]
        virt_comp = get_roots_from_filter(dict_tosca, child_key=vci[0], child_value=vci[1])
        virt_comp_key_list = [k for k in merge_list_of_dicts(virt_comp).keys()]
        virt_comp_mapping = self.generate_map_from_list(virt_comp_key_list)

        self.mapping = [
            # ** Metadata **
            ((vaT["descriptor_id"], self.FLAG_BLANK),        S.vnfd_id),
            ((vaT["descriptor_version"], self.FLAG_BLANK),   S.vnfd_ver),
            ((vaT["provider"], self.FLAG_BLANK),             S.vnfd_provider),
            ((vaT["product_name"], self.FLAG_BLANK),         S.vnfd_product),
            ((vaT["product_info_name"], self.FLAG_BLANK),    S.vnfd_info_name),
            ((vaT["product_info_desc"], self.FLAG_BLANK),    S.vnfd_info_desc),
            ((vaT["software_version"], self.FLAG_BLANK),     S.vnfd_software_ver),
            ((vaT["vnfm_info"], self.FLAG_BLANK),            S.vnfd_vnfm_info),

            ((vaT["virtual_compute_mem_size"], self.FLAG_ONLY_NUMBERS), [S.vnfd_vcd_mem_size,
                                                                         virt_comp_mapping]),



        ]


