from sol6_keys import *
from list_utils import *


class TOSCA(TOSCA_BASE):
    @staticmethod
    def set_variables(cur_dict, obj, exclude="", variables=None, dict_tosca=None,
                      cur_provider=None):
        """
        Take the input from the config file, and set the variables that are identifiers here
        This must be run before the values are used
        """
        if not cur_provider:
            cur_provider = get_path_value(variables["tosca"]["vnf_provider"], dict_tosca).lower()
        cur_provider = "-".join(cur_provider.split(" "))
        possible_providers = variables['providers']
        
        # We must have a provider mapping
        if cur_provider not in possible_providers:
            raise KeyError("Provider {} not found in possible providers {}"
                           .format(cur_provider, possible_providers))

        # Get the values for the given provider
        provider_identifiers = variables["provider_identifiers"][cur_provider]

        # Get the identifiers and assign them to the relevant locations
        # It is unlikely we will ever have sol6 identifiers
        variables["tosca"]["virtual_compute_identifier"] = provider_identifiers["virtual_compute"]
        variables["tosca"]["virtual_storage_identifier"] = provider_identifiers["virtual_storage"]
        variables["tosca"]["sw_image_identifier"] = provider_identifiers["sw_image"]
        variables["tosca"]["vdu_identifier"] = provider_identifiers["vdu"]
        variables["tosca"]["int_cpd_identifier"] = provider_identifiers["int_cpd"]
        variables["tosca"]["ext_cpd_identifier"] = provider_identifiers["ext_cpd"]
        variables["tosca"]["virtual_link_identifier"] = provider_identifiers["virtual_link"]


class SOL6(SOL6_BASE):
    pass


class V2Map(V2MapBase):
    def __init__(self, dict_tosca, dict_sol6, variables=None):
        super().__init__(dict_tosca, dict_sol6, c_log=log, variables=variables)

        # Make the lines shorter
        add_map = self.add_map
        self.tv = self.get_tosca_value
        self.sv = self.get_sol6_value
        tv = self.tv
        sv = self.sv

        # Virtual compute & storage mapping
        # Get a mapping based on a type from the whole dict
        virt_comp_mapping = self.generate_map(None, tv("virtual_compute_identifier"))
        virt_storage_mapping = self.generate_map(None, tv("virtual_storage_identifier"))
        sw_image_mapping = self.generate_map(None, tv("sw_image_identifier"))
        vdu_mapping = self.generate_map(None, tv("vdu_identifier"))

        # ** Connection point mappings **
        # Internal CP
        icp_mapping = self.generate_map(None, tv("int_cpd_identifier"),
                                        field_filter=self.icp_mapped)
        print(icp_mapping)

        # We have the icp mapping, which is
        # [oamICpd -> 0, parent=(None), ...]
        # Now we need to set the parent to the VDU mapping that matches cur_vdu
        for icp in icp_mapping:
            cur_vdu = get_path_value(MapElem.format_path(icp, tv("int_cpd_binding"),
                                                         use_value=False), dict_tosca)
            cur_vdu_map = MapElem.get_mapping_name(vdu_mapping, cur_vdu)
            MapElem.add_parent_mapping(icp, cur_vdu_map)

        # External CP
        ecp_mapping = self.generate_map(None, tv("ext_cpd_identifier"))
        ecp_icp_vdus = self.generate_map(None, tv("ext_cpd_identifier"))

        # Map ext cpds to connected ICPs then get the VDUs from those ICPs
        for ecp in ecp_icp_vdus:
            cur_icp = get_path_value(
                MapElem.format_path(ecp, tv("ext_cpd_icps"), use_value=False),
                dict_tosca, must_exist=False, no_msg=True)
            if not cur_icp:
                continue
            # These are the ICPs that this ECP is connected to
            # Get the VDUs they are connected to, and assign the parent of the ECP to that
            cur_icp_map = MapElem.get_mapping_name(icp_mapping, cur_icp)

            if not cur_icp_map:  # Make sure the VDU exists (it should)
                log.warning("Internal connection point {} parent VDU not found".format(cur_icp))
                continue
            MapElem.add_parent_mapping(ecp, cur_icp_map.parent_map)
            ecp.name = None  # Skip the ecp name so we can output the vdu (parent's) name

        # Virtual Link mapping
        virt_link_mapping = self.generate_map(None, tv("virtual_link_identifier"))

        # ** Virtual Compute, Virtual Storage, Software mappings **
        vdu_vc_mapping = []
        vdu_vs_mapping = []
        vdu_sw_mapping = []
        # TOSCA path only has one variable to fill, but SOL6 has 2.
        # This means we need to skip the first one in TOSCA, so set the key to none with none_key
        for vdu in vdu_mapping:
            vc_path = MapElem.format_path(vdu, tv("vdu_req_virt_compute"), use_value=False)
            vs_path = MapElem.format_path(vdu, tv("vdu_req_virt_storage"), use_value=False)
            sw_path = MapElem.format_path(vdu, tv("vdu_req_sw_image"), use_value=False)

            vdu_vc_mapping.append(self.generate_map(vc_path, None, cur_dict=dict_tosca, parent=vdu,
                                                    map_args={"none_key": True}))
            vdu_vs_mapping.append(self.generate_map(vs_path, None, cur_dict=dict_tosca, parent=vdu,
                                                    map_args={"none_key": True}))
            vdu_sw_mapping.append(self.generate_map(sw_path, None, cur_dict=dict_tosca, parent=vdu,
                                                    map_args={"none_key": True}))
        vdu_vc_mapping = flatten(vdu_vc_mapping)
        vdu_vs_mapping = flatten(vdu_vs_mapping)
        vdu_sw_mapping = flatten(vdu_sw_mapping)

        # VDU Profile and instantiation levels mapping
        df_vdu_prof_map = self.generate_map(tv("df_vdu_profs"), None, cur_dict=dict_tosca)
        df_inst_levels_map = self.generate_map(tv("df_inst_levels"), None, cur_dict=dict_tosca)

        # Generate vdu_level map inside of instantiation_levels map
        df_inst_vdu_level_map = []
        for df_inst in df_inst_levels_map:
            cur_path = MapElem.format_path(df_inst, tv("df_inst_vdu_levels"), use_value=False)
            df_inst_vdu_level_map.append(self.generate_map(cur_path, None, cur_dict=dict_tosca,
                                                           parent=df_inst))
        df_inst_vdu_level_map = flatten(df_inst_vdu_level_map)  # Make sure it's a flat list

        add_map(((tv("descriptor_id"), self.FLAG_BLANK),        sv("vnfd_id")))

        # ** Metadata **
        add_map(((tv("software_version"), self.FLAG_BLANK),   sv("vnfd_ver")))
        add_map(((tv("provider"), self.FLAG_BLANK),           sv("vnfd_provider")))
        add_map(((tv("product_name"), self.FLAG_BLANK),       sv("vnfd_product")))
        add_map(((tv("product_info_name"), self.FLAG_BLANK),  sv("vnfd_info_name")))
        add_map(((tv("product_info_desc"), self.FLAG_BLANK),  sv("vnfd_info_desc")))
        add_map(((tv("software_version"), self.FLAG_BLANK),   sv("vnfd_software_ver")))
        add_map(((tv("vnfm_info"), self.FLAG_BLANK),          sv("vnfd_vnfm_info")))

        # ** Virtual Compute **
        add_map(((tv("virtual_compute"), self.FLAG_KEY_SET_VALUE),
                 [sv("vnfd_vcd_id"), virt_comp_mapping]))
        add_map(((tv("virtual_compute_mem_size"), self.FLAG_ONLY_NUMBERS),
                 [sv("vnfd_vcd_mem_size"), virt_comp_mapping]))
        add_map(((tv("virtual_compute_cpu_num"), self.FLAG_ONLY_NUMBERS),
                 [sv("vnfd_vcd_cpu_num"), virt_comp_mapping]))
        add_map(((tv("virtual_compute_cpu_arch"), self.FLAG_BLANK),
                 [sv("vnfd_vcd_cpu_arch"), virt_comp_mapping]))
        add_map(((tv("virtual_compute_cpu_clock"), self.FLAG_ONLY_NUMBERS),
                 [sv("vnfd_vcd_cpu_clock"), virt_comp_mapping]))

        # ** Virtual Storage **
        add_map(((tv("virtual_storage"), self.FLAG_KEY_SET_VALUE),
                 [sv("vnfd_virt_storage_id"), virt_storage_mapping]))
        add_map(((tv("virtual_storage_type"), self.FLAG_BLANK),
                 [sv("vnfd_virt_storage_type"), virt_storage_mapping]))
        add_map(((tv("virtual_storage_size"), self.FLAG_ONLY_NUMBERS),
                 [sv("vnfd_virt_storage_size"), virt_storage_mapping]))

        # ** SW Image **
        add_map(((tv("sw_image_r"), self.FLAG_KEY_SET_VALUE),  [sv("sw_id"), sw_image_mapping]))
        add_map(((tv("sw_image_name"), self.FLAG_BLANK),
                 [sv("sw_name"), sw_image_mapping]))
        add_map(((tv("sw_image_container_fmt"), (self.FLAG_FORMAT_CONT_FMT, self.FLAG_LIST_FIRST,
                                                 self.FLAG_FORMAT_INVALID_NONE)),
                [sv("sw_container_format"), sw_image_mapping]))
        add_map(((tv("sw_image_version"), self.FLAG_BLANK),
                 [sv("sw_version"), sw_image_mapping]))
        add_map(((tv("sw_image_checksum"), self.FLAG_BLANK),
                 [sv("sw_checksum"), sw_image_mapping]))
        add_map(((tv("sw_image_min_disk"), self.FLAG_ONLY_NUMBERS),
                 [sv("sw_min_disk"), sw_image_mapping]))
        add_map(((tv("sw_image_min_ram"), self.FLAG_ONLY_NUMBERS),
                 [sv("sw_min_ram"), sw_image_mapping]))
        add_map(((tv("sw_image_size"), self.FLAG_ONLY_NUMBERS),
                 [sv("sw_size"), sw_image_mapping]))
        add_map(((tv("sw_image_disk_fmt"), (self.FLAG_FORMAT_DISK_FMT, self.FLAG_LIST_FIRST,
                                            self.FLAG_FORMAT_INVALID_NONE)),
                [sv("sw_disk_format"), sw_image_mapping]))
        add_map(((tv("sw_image_sw_image"), self.FLAG_BLANK),
                 [sv("sw_image_name_var"), sw_image_mapping]))
        add_map(((tv("sw_image_sw_image"), self.FLAG_BLANK),
                 [sv("sw_image"), sw_image_mapping]))
        add_map(((tv("sw_image_operating_system"), self.FLAG_BLANK),
                 [sv("sw_operating_sys"), sw_image_mapping]))
        add_map(((tv("sw_image_supp_virt_environs"), self.FLAG_BLANK),
                 [sv("sw_supp_virt_environ"), sw_image_mapping]))

        # ** VDU **
        add_map(((tv("vdu"), self.FLAG_KEY_SET_VALUE),    [sv("vdu_id"), vdu_mapping]))
        add_map(((tv("vdu"), self.FLAG_KEY_SET_VALUE),    [sv("vdu_name"), vdu_mapping]))
        add_map(((tv("vdu_desc"), self.FLAG_BLANK),       [sv("vdu_desc"), vdu_mapping]))
        add_map(((tv("vdu_req_virt_compute"), self.FLAG_BLANK),
                 [sv("vdu_vc_desc"), vdu_vc_mapping]))
        add_map(((tv("vdu_req_virt_storage"), self.FLAG_BLANK),
                 [sv("vdu_vs_desc"), vdu_vs_mapping]))
        add_map(((tv("vdu_req_sw_image"), self.FLAG_BLANK),
                 [sv("vdu_sw_image_desc"), vdu_sw_mapping]))

        # ** Deployment Flavor **
        add_map(((tv("df_id"), self.FLAG_BLANK), sv("df_id")))
        # VDU Profiles
        add_map(((tv("df_vdu_prof"), self.FLAG_KEY_SET_VALUE),
                 [sv("df_vdu_prof_id"), df_vdu_prof_map]))
        add_map(((tv("df_vdu_prof_min_inst"), self.FLAG_BLANK),
                 [sv("df_vdu_prof_inst_min"), df_vdu_prof_map]))
        add_map(((tv("df_vdu_prof_max_inst"), self.FLAG_BLANK),
                 [sv("df_vdu_prof_inst_max"), df_vdu_prof_map]))

        add_map(((tv("df_inst_level_default"), self.FLAG_BLANK), sv("df_inst_level_default")))
        # Instantiation Levels
        add_map(((tv("df_inst_level"), self.FLAG_KEY_SET_VALUE),
                 [sv("df_inst_level_id"), df_inst_levels_map]))
        add_map(((tv("df_inst_vdu_level"), self.FLAG_KEY_SET_VALUE),
                 [sv("df_inst_level_vdu_vdu"), df_inst_vdu_level_map]))
        add_map(((tv("df_inst_vdu_level_num"), self.FLAG_BLANK),
                 [sv("df_inst_level_vdu_num"), df_inst_vdu_level_map]))

        # ** Connection Points **
        # Internal CPs
        add_map(((tv("int_cpd"), self.FLAG_KEY_SET_VALUE),
                 [sv("int_cpd_id"), icp_mapping]))
        add_map(((tv("int_cpd_protocol"), self.FLAG_FORMAT_IP),
                 [sv("int_cpd_layer_prot"), icp_mapping]))
        add_map(((tv("int_cpd_role"), self.FLAG_BLANK),
                 [sv("int_cpd_role"), icp_mapping]))
        # Interface id, with incrementing number, use the sol6 array index
        add_map(((tv("int_cpd"), (self.FLAG_KEY_SET_VALUE,
                                  self.FLAG_USE_VALUE, self.FLAG_ONLY_NUMBERS)),
                [sv("int_cpd_interface_id"), icp_mapping]))
        # Map the virtual link descriptors, but expect that some don't have the links, so suppress
        # warning messages
        add_map(((tv("int_cpd_link"), self.FLAG_FAIL_SILENT),
                 [sv("int_cpd_virt_link_desc"), icp_mapping]))

        # External CPs
        add_map(((tv("ext_cpd"), self.FLAG_KEY_SET_VALUE),
                 [sv("ext_cpd_id"), ecp_mapping]))
        add_map(((tv("ext_cpd_protocol"), self.FLAG_FORMAT_IP),
                 [sv("ext_cpd_protocol"), ecp_mapping]))
        add_map(((tv("ext_cpd_icps"), self.FLAG_BLANK),
                 [sv("ext_cpd_int_cpd_id"), ecp_mapping]))
        # Outputting the VDU the ICP is a part of
        add_map(((tv("ext_cpd"), (self.FLAG_KEY_SET_VALUE, self.FLAG_REQ_PARENT)),
                [sv("ext_cpd_vdu_id"), ecp_icp_vdus]))

        add_map(((tv("ext_cpd_role"), self.FLAG_BLANK),
                 [sv("ext_cpd_role"), ecp_mapping]))

        # Virtual Links
        add_map(((tv("virt_link"), self.FLAG_KEY_SET_VALUE),
                 [sv("virt_link_desc_id"), virt_link_mapping]))
        add_map(((tv("virt_link_desc"), self.FLAG_BLANK),
                 [sv("virt_link_desc_desc"), virt_link_mapping]))
        add_map(((tv("virt_link_protocol"), self.FLAG_FORMAT_IP),
                 [sv("virt_link_desc_protocol"), virt_link_mapping]))
        add_map(((tv("virt_link_flow_pattern"), self.FLAG_BLANK),
                 [sv("virt_link_desc_flow"), virt_link_mapping]))

    # ----------------------------------------------------------------------------------------------

    def icp_mapped(self, a):
        """Check if the given int_cpd has the required value"""
        return get_path_value(self.tv("int_cpd_cond").format(SPLIT_CHAR), a[get_dict_key(a)], must_exist=False,
                              no_msg=True)

