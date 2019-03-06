from sol6_keys import *
from list_utils import *


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
        variables["tosca"]["vdu_identifier"] = provider_identifiers["vdu"]
        variables["tosca"]["int_cpd_identifier"] = provider_identifiers["int-cpd"]
        variables["tosca"]["ext_cpd_identifier"] = provider_identifiers["ext-cpd"]


class SOL6(SOL6_BASE):
    pass


class V2Map(V2Map):
    def __init__(self, dict_tosca, dict_sol6, variables=None, log=None):
        super().__init__(dict_tosca, dict_sol6, log=log)
        va_t = variables["tosca"]
        va_s = variables["sol6"]
        self.va_t = va_t
        self.va_s = va_s

        # Virtual compute & storage mapping
        # Get a mapping based on a type from the whole dict
        virt_comp_mapping = self.generate_map(None, va_t["virtual_compute_identifier"])
        virt_storage_mapping = self.generate_map(None, va_t["virtual_storage_identifier"])
        sw_image_mapping = self.generate_map(None, va_t["sw_image_identifier"])
        vdu_mapping = self.generate_map(None, va_t["vdu_identifier"])
        va_t["int_cpd_identifier"].append(self.icp_mapped)
        icp_mapping = self.generate_map(None, va_t["int_cpd_identifier"])
        ecp_mapping = self.generate_map(None, va_t["ext_cpd_identifier"])

        # We have the icp mapping, which is
        # [oamICpd -> 0, parent=(None), ...]
        # Now we need to set the parent to the VDU mapping that matches cur_vdu
        for icp in icp_mapping:
            cur_vdu = get_path_value(MapElem.format_path(icp, va_t["int_cpd_binding"],
                                                         use_value=False), dict_tosca)
            cur_vdu_map = MapElem.get_mapping_name(vdu_mapping, cur_vdu)
            MapElem.add_parent_mapping(icp, cur_vdu_map)

        print(icp_mapping)

        vdu_vc_mapping = None
        vdu_vs_mapping = None
        vdu_sw_mapping = None
        # TOSCA path only has one variable to fill, but SOL6 has 2.
        # This means we need to skip the first one in TOSCA, so set the key to none with none_key
        # TODO: I think this will fail with multiple VDUs
        for vdu in vdu_mapping:
            vc_path = MapElem.format_path(vdu, va_t["vdu_req_virt_compute"], use_value=False)
            vs_path = MapElem.format_path(vdu, va_t["vdu_req_virt_storage"], use_value=False)
            sw_path = MapElem.format_path(vdu, va_t["vdu_req_sw_image"], use_value=False)

            vdu_vc_mapping = self.generate_map(vc_path, None, cur_dict=dict_tosca, parent=vdu,
                                               map_args={"none_key": True})
            vdu_vs_mapping = self.generate_map(vs_path, None, cur_dict=dict_tosca, parent=vdu,
                                               map_args={"none_key": True})
            vdu_sw_mapping = self.generate_map(sw_path, None, cur_dict=dict_tosca, parent=vdu,
                                               map_args={"none_key": True})

        df_vdu_prof_map = self.generate_map(va_t["df_vdu_profs"], None, cur_dict=dict_tosca)
        df_inst_levels_map = self.generate_map(va_t["df_inst_levels"], None, cur_dict=dict_tosca)

        # Generate vdu_level map inside of instantiation_levels map
        df_inst_vdu_level_map = []
        for df_inst in df_inst_levels_map:
            cur_path = MapElem.format_path(df_inst, va_t["df_inst_vdu_levels"], use_value=False)
            df_inst_vdu_level_map.append(self.generate_map(cur_path, None, cur_dict=dict_tosca,
                                                           parent=df_inst))
        df_inst_vdu_level_map = flatten(df_inst_vdu_level_map)  # Make sure it's a flat list

        # Make the lines shorter
        add_map = self.add_map

        # TODO: Make handling errors here easier
        add_map(((va_t["descriptor_id"], self.FLAG_BLANK),        va_s["vnfd_id"]))

        # ** Metadata **
        add_map(((va_t["software_version"], self.FLAG_BLANK),   va_s["vnfd_ver"]))
        add_map(((va_t["provider"], self.FLAG_BLANK),           va_s["vnfd_provider"]))
        add_map(((va_t["product_name"], self.FLAG_BLANK),       va_s["vnfd_product"]))
        add_map(((va_t["product_info_name"], self.FLAG_BLANK),  va_s["vnfd_info_name"]))
        add_map(((va_t["product_info_desc"], self.FLAG_BLANK),  va_s["vnfd_info_desc"]))
        add_map(((va_t["software_version"], self.FLAG_BLANK),   va_s["vnfd_software_ver"]))
        add_map(((va_t["vnfm_info"], self.FLAG_BLANK),          va_s["vnfd_vnfm_info"]))

        # ** Virtual Compute **
        add_map(((va_t["virtual_compute"], self.FLAG_KEY_SET_VALUE),
                 [va_s["vnfd_vcd_id"], virt_comp_mapping]))
        add_map(((va_t["virtual_compute_mem_size"], self.FLAG_ONLY_NUMBERS),
                 [va_s["vnfd_vcd_mem_size"], virt_comp_mapping]))
        add_map(((va_t["virtual_compute_cpu_num"], self.FLAG_ONLY_NUMBERS),
                 [va_s["vnfd_vcd_cpu_num"], virt_comp_mapping]))
        add_map(((va_t["virtual_compute_cpu_arch"], self.FLAG_BLANK),
                 [va_s["vnfd_vcd_cpu_arch"], virt_comp_mapping]))
        add_map(((va_t["virtual_compute_cpu_clock"], self.FLAG_BLANK),
                 [va_s["vnfd_vcd_cpu_clock"], virt_comp_mapping]))

        # ** Virtual Storage **
        add_map(((va_t["virtual_storage"], self.FLAG_KEY_SET_VALUE),
                 [va_s["vnfd_virt_storage_id"], virt_storage_mapping]))
        add_map(((va_t["virtual_storage_type"], self.FLAG_BLANK),
                 [va_s["vnfd_virt_storage_type"], virt_storage_mapping]))
        add_map(((va_t["virtual_storage_size"], self.FLAG_ONLY_NUMBERS),
                 [va_s["vnfd_virt_storage_size"], virt_storage_mapping]))

        # ** SW Image **
        add_map(((va_t["sw_image_r"], self.FLAG_KEY_SET_VALUE),  [va_s["sw_id"], sw_image_mapping]))
        add_map(((va_t["sw_image_name"], self.FLAG_BLANK),
                 [va_s["sw_name"], sw_image_mapping]))
        add_map(((va_t["sw_image_container_fmt"], self.FLAG_BLANK),
                 [va_s["sw_container_format"], sw_image_mapping]))
        add_map(((va_t["sw_image_version"], self.FLAG_BLANK),
                 [va_s["sw_version"], sw_image_mapping]))
        add_map(((va_t["sw_image_checksum"], self.FLAG_BLANK),
                 [va_s["sw_checksum"], sw_image_mapping]))
        add_map(((va_t["sw_image_min_disk"], self.FLAG_ONLY_NUMBERS),
                 [va_s["sw_min_disk"], sw_image_mapping]))
        add_map(((va_t["sw_image_min_ram"], self.FLAG_ONLY_NUMBERS),
                 [va_s["sw_min_ram"], sw_image_mapping]))
        add_map(((va_t["sw_image_size"], self.FLAG_ONLY_NUMBERS),
                 [va_s["sw_size"], sw_image_mapping]))
        add_map(((va_t["sw_image_disk_fmt"], self.FLAG_BLANK),
                 [va_s["sw_disk_format"], sw_image_mapping]))
        add_map(((va_t["sw_image_sw_image"], self.FLAG_BLANK),
                 [va_s["sw_image_name_var"], sw_image_mapping]))
        add_map(((va_t["sw_image_operating_system"], self.FLAG_BLANK),
                 [va_s["sw_operating_sys"], sw_image_mapping]))
        add_map(((va_t["sw_image_supp_virt_environs"], self.FLAG_BLANK),
                 [va_s["sw_supp_virt_environ"], sw_image_mapping]))

        # ** VDU **
        add_map(((va_t["vdu"], self.FLAG_KEY_SET_VALUE),    [va_s["vdu_id"], vdu_mapping]))
        add_map(((va_t["vdu"], self.FLAG_KEY_SET_VALUE),    [va_s["vdu_name"], vdu_mapping]))
        add_map(((va_t["vdu_desc"], self.FLAG_BLANK),       [va_s["vdu_desc"], vdu_mapping]))
        add_map(((va_t["vdu_req_virt_compute"], self.FLAG_BLANK),
                 [va_s["vdu_vc_desc"], vdu_vc_mapping]))
        add_map(((va_t["vdu_req_virt_storage"], self.FLAG_BLANK),
                 [va_s["vdu_vs_desc"], vdu_vs_mapping]))
        add_map(((va_t["vdu_req_sw_image"], self.FLAG_BLANK),
                 [va_s["vdu_sw_image_desc"], vdu_sw_mapping]))

        # ** Deployment Flavor **
        add_map(((va_t["df_id"], self.FLAG_BLANK), va_s["df_id"]))
        # VDU Profiles
        add_map(((va_t["df_vdu_profs"], self.FLAG_KEY_SET_VALUE),
                 [va_s["df_vdu_prof_id"], df_vdu_prof_map]))
        add_map(((va_t["df_vdu_prof_min_inst"], self.FLAG_BLANK),
                 [va_s["df_vdu_prof_inst_min"], df_vdu_prof_map]))
        add_map(((va_t["df_vdu_prof_max_inst"], self.FLAG_BLANK),
                 [va_s["df_vdu_prof_inst_max"], df_vdu_prof_map]))

        add_map(((va_t["df_inst_level_default"], self.FLAG_BLANK), va_s["df_inst_level_default"]))
        # Instantiation Levels
        add_map(((va_t["df_inst_level"], self.FLAG_KEY_SET_VALUE),
                 [va_s["df_inst_level_id"], df_inst_levels_map]))
        add_map(((va_t["df_inst_vdu_level"], self.FLAG_KEY_SET_VALUE),
                 [va_s["df_inst_level_vdu_vdu"], df_inst_vdu_level_map]))
        add_map(((va_t["df_inst_vdu_level_num"], self.FLAG_BLANK),
                 [va_s["df_inst_level_vdu_num"], df_inst_vdu_level_map]))

        # ** Connection Points **
        # Internal CPs
        add_map(((va_t["int_cpd"], self.FLAG_KEY_SET_VALUE),
                 [va_s["int_cpd_id"], icp_mapping]))
        add_map(((va_t["int_cpd_protocol"], self.FLAG_FORMAT_IP),
                 [va_s["int_cpd_layer_prot"], icp_mapping]))
        add_map(((va_t["int_cpd_role"], self.FLAG_BLANK),
                 [va_s["int_cpd_role"], icp_mapping]))
        # Interface id, with incrementing number, use the sol6 array index
        add_map(((va_t["int_cpd"],
                  (self.FLAG_KEY_SET_VALUE, self.FLAG_USE_VALUE, self.FLAG_ONLY_NUMBERS)),
                 [va_s["int_cpd_interface_id"], icp_mapping]))

    def icp_mapped(self, a):
        """Check if the given int_cpd has the required value"""
        return get_path_value(self.va_t["int_cpd_cond"], a[get_dict_key(a)], must_exist=False,
                              no_msg=True)
