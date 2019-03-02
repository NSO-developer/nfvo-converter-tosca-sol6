from sol6_keys import *


class TOSCA(TOSCA_BASE):
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

        # Get the values for the given provider
        provider_identifiers = variables["provider-identifiers"][cur_provider]

        # Get the identifiers and assign them to the relevant locations
        # It is unlikely we will ever have sol6 identifiers
        variables["tosca"]["virtual_compute_identifier"] = provider_identifiers["virtual-compute"]
        variables["tosca"]["virtual_storage_identifier"] = provider_identifiers["virtual-storage"]
        variables["tosca"]["sw_image_identifier"] = provider_identifiers["sw-image"]


class SOL6(SOL6_BASE):
    pass


class V2Map(V2Map):
    def __init__(self, dict_tosca, dict_sol6, variables=None, log=None):
        super().__init__(dict_tosca, dict_sol6, log=log)
        vaT = variables["tosca"]
        vaS = variables["sol6"]
        S = SOL6

        # Virtual compute & storage mapping
        # Get a mapping based on a type from the whole dict
        virt_comp_mapping = self.generate_map(None, vaT["virtual_compute_identifier"])
        virt_storage_mapping = self.generate_map(None, vaT["virtual_storage_identifier"])
        sw_image_mapping = self.generate_map(None, vaT["sw_image_identifier"])

        self.mapping = [
            # ** Metadata **
            ((vaT["descriptor_id"], self.FLAG_BLANK),        vaS["vnfd_id"]),
            ((vaT["descriptor_version"], self.FLAG_BLANK),   vaS["vnfd_ver"]),
            ((vaT["provider"], self.FLAG_BLANK),             vaS["vnfd_provider"]),
            ((vaT["product_name"], self.FLAG_BLANK),         vaS["vnfd_product"]),
            ((vaT["product_info_name"], self.FLAG_BLANK),    vaS["vnfd_info_name"]),
            ((vaT["product_info_desc"], self.FLAG_BLANK),    vaS["vnfd_info_desc"]),
            ((vaT["software_version"], self.FLAG_BLANK),     vaS["vnfd_software_ver"]),
            ((vaT["vnfm_info"], self.FLAG_BLANK),            vaS["vnfd_vnfm_info"]),


            ((vaT["virtual_compute"], self.FLAG_KEY_SET_VALUE),
             [vaS["vnfd_vcd_id"], virt_comp_mapping]),

            ((vaT["virtual_compute_mem_size"], self.FLAG_ONLY_NUMBERS),
             [vaS["vnfd_vcd_mem_size"], virt_comp_mapping]),

            ((vaT["virtual_compute_cpu_num"], self.FLAG_ONLY_NUMBERS),
             [vaS["vnfd_vcd_cpu_num"], virt_comp_mapping]),

            ((vaT["virtual_compute_cpu_arch"], self.FLAG_BLANK),
             [vaS["vnfd_vcd_cpu_arch"], virt_comp_mapping]),

            ((vaT["virtual_compute_cpu_clock"], self.FLAG_BLANK),
             [vaS["vnfd_vcd_cpu_clock"], virt_comp_mapping]),


            ((vaT["virtual_storage"], self.FLAG_KEY_SET_VALUE),
             [vaS["vnfd_virt_storage_id"], virt_storage_mapping]),

            ((vaT["virtual_storage_type"], self.FLAG_BLANK),
             [vaS["vnfd_virt_storage_type"], virt_storage_mapping]),

            ((vaT["virtual_storage_size"], self.FLAG_ONLY_NUMBERS),
             [vaS["vnfd_virt_storage_size"], virt_storage_mapping]),


            ((vaT["sw_image_r"], self.FLAG_KEY_SET_VALUE),  [vaS["sw_id"], sw_image_mapping]),
            ((vaT["sw_image_name"], self.FLAG_BLANK),       [vaS["sw_name"], sw_image_mapping]),
            ((vaT["sw_image_container_fmt"], self.FLAG_BLANK),
             [vaS["sw_container_format"], sw_image_mapping]),

            ((vaT["sw_image_version"], self.FLAG_BLANK),    [vaS["sw_version"], sw_image_mapping]),
            ((vaT["sw_image_checksum"], self.FLAG_BLANK),   [vaS["sw_checksum"], sw_image_mapping]),
            ((vaT["sw_image_min_disk"], self.FLAG_ONLY_NUMBERS),
             [vaS["sw_min_disk"], sw_image_mapping]),

            ((vaT["sw_image_min_ram"], self.FLAG_ONLY_NUMBERS),
             [vaS["sw_min_ram"], sw_image_mapping]),

            ((vaT["sw_image_size"], self.FLAG_ONLY_NUMBERS), [vaS["sw_size"], sw_image_mapping]),
            ((vaT["sw_image_disk_fmt"], self.FLAG_BLANK),
             [vaS["sw_disk_format"], sw_image_mapping]),

            ((vaT["sw_image_sw_image"], self.FLAG_BLANK),
             [vaS["sw_image_name_var"], sw_image_mapping]),

            ((vaT["sw_image_operating_system"], self.FLAG_BLANK),
             [vaS["sw_operating_sys"], sw_image_mapping]),

            ((vaT["sw_image_supp_virt_environs"], self.FLAG_BLANK),
             [vaS["sw_supp_virt_environ"], sw_image_mapping]),





        ]


