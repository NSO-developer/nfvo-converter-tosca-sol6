"""
These are automatically used without having to update anything else.
The TOSCA variables are mapped to the SOL6 ones, they must have the same names.
The program does not attempt to map variables beginning with '_'
"""
from mapping_v2 import V2Mapping, MapElem
from dict_utils import *
from list_utils import *


class TOSCAv2:
    """
    Second version of the definitions
    """
    topology_template               = "topology_template"
    node_template                   = topology_template + ".node_templates"
    desc                            = "description"
    policies                        = topology_template + ".policies"
    inputs                          = "topology_template.inputs"
    input_key                       = "get_input"

    # **************
    # ** Metadata **
    # **************
    vnf                             = node_template + ".vnf"
    vnf_prop                        = vnf + ".properties"
    vnf_desc_id                     = vnf_prop + ".descriptor_id"
    vnf_desc_ver                    = vnf_prop + ".descriptor_version"
    vnf_provider                    = vnf_prop + ".provider"
    vnf_product_name                = vnf_prop + ".product_name"
    vnf_software_ver                = vnf_prop + ".software_version"
    vnf_product_info_name           = vnf_prop + ".product_info_name"
    vnf_vnfm_info                   = vnf_prop + ".vnfm_info"

    # *********
    # ** VDU **
    # *********
    vdu                             = node_template + ".{}"
    vdu_identifier                  = ["type", "cisco.nodes.nfv.Vdu.Compute"]
    vdu_props                       = vdu + ".properties"
    vdu_name                        = vdu_props + ".name"
    vdu_boot                        = vdu_props + ".boot_order"
    vdu_desc                        = vdu_props + ".description"
    vdu_conf_props                  = vdu_props + ".configurable_properties." \
                                                  "additional_vnfc_configurable_properties"
    vdu_vim_flavor                  = vdu_conf_props + ".vim_flavor"
    vdu_cap_props                   = vdu + ".capabilities.virtual_compute.properties"
    vdu_virt_cpu_num                = vdu_cap_props + ".virtual_cpu.num_virtual_cpu"
    vdu_virt_mem_size               = vdu_cap_props + ".virtual_memory.virtual_mem_size"

    vdu_profile                     = vdu_props + ".vdu_profile"
    vdu_prof_inst_min               = vdu_profile + ".min_number_of_instances"
    vdu_prof_inst_max               = vdu_profile + ".max_number_of_instances"

    # *********************************
    # ** Internal Connectiion Points **
    # *********************************
    @staticmethod
    def int_cp_mgmt(item):
        """Return if the current cp is assigned to management or not"""
        return key_exists(item, "properties.management") and \
            get_path_value("properties.management", item[get_dict_key(item)], must_exist=False)

    int_cpd                         = node_template + ".{}"
    int_cpd_identifier              = ["type", "cisco.nodes.nfv.VduCp"]
    int_cpd_mgmt_identifier         = ["type", "cisco.nodes.nfv.VduCp", int_cp_mgmt.__func__]
    int_cpd_props                   = int_cpd + ".properties"
    int_cpd_virt_binding            = int_cpd + ".requirements.virtual_binding"
    int_cpd_virt_link               = int_cpd + ".requirements.virtual_link"
    int_cpd_layer_prot              = int_cpd_props + ".layer_protocols"

    @staticmethod
    def virt_filter(item):
        # Make sure that the virtual storage block we get has the {}.properties.sw_image_data field
        return key_exists(item, "properties.sw_image_data")

    virt_storage                    = node_template + ".{}"
    virt_storage_identifier         = ["type", "cisco.nodes.nfv.Vdu.VirtualBlockStorage",
                                       virt_filter.__func__]
    virt_props                      = virt_storage + ".properties"
    virt_artifacts                  = virt_storage + ".artifacts"
    virt_vsb                        = virt_props + ".virtual_block_storage_data"
    virt_size                       = virt_props + ".size_of_storage"
    sw_image_data                   = virt_props + ".sw_image_data"
    sw_name                         = sw_image_data + ".name"
    sw_version                      = sw_image_data + ".version"
    sw_checksum                     = sw_image_data + ".checksum"
    sw_container_fmt                = sw_image_data + ".container_format"
    sw_disk_fmt                     = sw_image_data + ".disk_format"
    sw_min_disk                     = sw_image_data + ".min_disk"
    sw_size                         = sw_image_data + ".size"
    sw_image_file                   = virt_artifacts + ".sw_image.file"

    # ***********************
    # ** Deployment Flavor **
    # ***********************

    df_id                           = vnf_prop + ".flavour_id"
    df_desc                         = vnf_prop + ".flavour_description"

    def_inst_level                  = policies + ".instantiation_levels"
    def_inst_key                    = "default"
    def_inst_prop                   = def_inst_level + ".properties.levels"
    def_inst_desc                   = def_inst_prop + "." + def_inst_key + ".description"
    inst_level_identifier           = ["type", "tosca.policies.nfv.VduInstantiationLevels"]
    inst_level                      = policies + ".{}"
    inst_level_targets              = inst_level + ".targets"
    inst_level_num_instances        = inst_level + ".properties.levels.default.number_of_instances"

    # Scaling Aspects
    scaling_aspects                 = policies + ".{}"
    scaling_aspects_identifier      = ["type", "tosca.policies.nfv.ScalingAspects"]
    scaling_props                   = scaling_aspects + ".properties"
    scaling_aspect_item_list        = scaling_props + ".aspects"
    scaling_aspect_item             = scaling_aspect_item_list + ".{}"
    scaling_aspect_name             = scaling_aspect_item + ".name"
    scaling_aspect_desc             = scaling_aspect_item + ".description"
    scaling_aspect_level            = scaling_aspect_item + ".max_scale_level"
    scaling_aspect_deltas           = scaling_aspect_item + ".step_deltas"
    # Note: this is not a valid TOSCA path, it's for internal use
    scaling_aspect_deltas_num       = scaling_aspect_item + ".deltas.{}.number_of_instances"


class SOL6v2:
    """
    Second version of the definitions
    """
    # **********
    # ** VNFD **
    # **********
    vnfd                            = "vnfd"
    vnfd_id                         = vnfd + ".id"
    vnfd_provider                   = vnfd + ".provider"
    vnfd_product                    = vnfd + ".product-name"
    vnfd_software_ver               = vnfd + ".software-version"
    vnfd_ver                        = vnfd + ".version"
    vnfd_info_name                  = vnfd + ".product-info-name"
    vnfd_info_desc                  = vnfd + ".product-info-description"
    vnfd_vnfm_info                  = vnfd + ".vnfm-info"

    VALID_PROTOCOLS = ["Ethernet", "IPv4", "IPv6", "MPLS", "ODU2", "Pseudo-Wire"]

    # ********************************
    # ** Virtual Compute Descriptor **
    # ********************************
    vnfd_virt_compute_desc          = vnfd + ".virtual-compute-descriptor.{}"
    vnfd_vcd_id                     = vnfd_virt_compute_desc + ".id"
    vnfd_vcd_flavor_name            = vnfd_virt_compute_desc + ".flavor-name-variable"
    vnfd_vcd_cpu_num                = vnfd_virt_compute_desc + ".virtual-cpu.num-virtual-cpu"
    vnfd_vcd_mem_size               = vnfd_virt_compute_desc + ".virtual-memory.size"

    # ********************************
    # ** Virtual Storage Descriptor **
    # ********************************
    vnfd_virt_storage_desc          = vnfd + ".virtual-storage-descriptor.{}"
    vnfd_virt_storage_id            = vnfd_virt_storage_desc + ".id"
    vnfd_virt_storage_type          = vnfd_virt_storage_desc + ".type-of-storage"
    vnfd_virt_storage_size          = vnfd_virt_storage_desc + ".size-of-storage"

    # ***********************
    # ** Deployment Flavor **
    # ***********************
    deployment_flavor               = vnfd + ".df"
    df_id                           = deployment_flavor + ".id"
    df_desc                         = deployment_flavor + ".description"
    df_vdu_profile                  = deployment_flavor + ".vdu-profile.{}"
    df_vdu_prof_id                  = df_vdu_profile + ".id"
    df_vdu_prof_inst_min            = df_vdu_profile + ".min-number-of-instances"
    df_vdu_prof_inst_max            = df_vdu_profile + ".max-number-of-instances"
    # -- Instantiation Level
    df_inst_level                   = deployment_flavor + ".instantiation-level"
    df_inst_level_id                = df_inst_level + ".id"
    df_inst_level_desc              = df_inst_level + ".description"
    df_inst_level_vdu_level         = df_inst_level + ".vdu-level.{}"
    df_inst_level_vdu_vdu           = df_inst_level_vdu_level + ".id"
    df_inst_level_vdu_num           = df_inst_level_vdu_level + ".number-of-instances"
    # - Scaling Info
    df_inst_scaling_info            = df_inst_level + ".scaling-info.{}"
    df_inst_scaling_aspect          = df_inst_scaling_info + ".id"
    df_inst_scaling_level           = df_inst_scaling_info + ".scale-level"

    df_scale_aspect                 = deployment_flavor + ".scaling-aspect.{}"
    df_scale_aspect_id              = df_scale_aspect + ".id"
    df_scale_aspect_name            = df_scale_aspect + ".name"
    df_scale_aspect_desc            = df_scale_aspect + ".description"
    df_scale_aspect_max_level       = df_scale_aspect + ".max-scale-level"
    df_scale_aspect_deltas          = df_scale_aspect + ".deltas"
    df_scale_aspect_vdu_delta       = df_scale_aspect + ".vdu-delta.{}"
    df_scale_aspect_vdu_id          = df_scale_aspect_vdu_delta + ".id"
    df_scale_aspect_vdu_num         = df_scale_aspect_vdu_delta + ".number-of-instances"

    # ****************************
    # ** Virtual/External Links **
    # ****************************
    virt_link_desc_id               = vnfd + ".int-virtual-link-desc.{}.id"

    ext_cpd                         = vnfd + ".ext-cpd.{}"
    ext_cpd_id                      = ext_cpd + ".id"
    ext_cpd_virt_link               = ext_cpd + ".int-virtual-link-desc"

    # *********
    # ** VDU **
    # *********
    vdus                            = vnfd + ".vdu"
    vdu                             = vdus + ".{}"
    vdu_name                        = vdu + ".name"
    vdu_desc                        = vdu + ".description"
    vdu_id                          = vdu + ".id"
    vdu_boot_order                  = vdu + ".boot-order.{}"
    vdu_boot_key                    = vdu_boot_order + ".key"
    vdu_boot_value                  = vdu_boot_order + ".value"
    vdu_vc_desc                     = vdu + ".virtual-compute-desc.{}"

    # *********************************
    # ** Internal Connection Points **
    # *********************************
    int_cpd                         = vdu + ".int-cpd.{}"
    int_cpd_id                      = int_cpd + ".id"
    int_cpd_layer_prot              = int_cpd + ".layer-protocol"
    int_cpd_virt_link_desc          = int_cpd + ".int-virtual-link-desc"

    KEY_VIRT_LINK_MGMT              = "CP_MGMT"
    KEY_VIRT_LINK_ORCH              = "CP_ORCH"
    KEY_EXT_CP_MGMT                 = "CP_EXT_MGMT"
    KEY_EXT_CP_ORCH                 = "CP_EXT_ORCH"

    # *******************************
    # ** Software Image Descriptor **
    # *******************************
    sw_img_desc                     = vnfd + ".sw-image-desc.{}"
    sw_id                           = sw_img_desc + ".id"
    sw_name                         = sw_img_desc + ".name"
    sw_image_name_var               = sw_img_desc + ".image_name_variable"
    sw_version                      = sw_img_desc + ".version"
    sw_checksum                     = sw_img_desc + ".checksum"
    sw_container_format             = sw_img_desc + ".container-format"
    sw_disk_format                  = sw_img_desc + ".disk-format"
    sw_min_disk                     = sw_img_desc + ".min-disk"
    sw_size                         = sw_img_desc + ".size"
    sw_image                        = sw_img_desc + ".image"


class V2Map(V2Mapping):
    """

    """
    FLAG_BLANK                      = ""
    # Pass this flag if you want to set the value with the key and not the value
    FLAG_KEY_SET_VALUE              = "KSV"
    # Will remove all non-numeric characters
    FLAG_ONLY_NUMBERS               = "NUMBERS"
    FLAG_ONLY_NUMBERS_FLOAT         = "NUMBERSFLOAT"
    # Make the tosca MapElem format use the value of the mapping instead of the key
    FLAG_USE_VALUE                  = "USESOLMAPFORTOSCA"
    # Append the items to a list, create the list if it doesn't exist
    FLAG_APPEND_LIST                = "APPENDLIST"
    # Get the first element in the input list
    FLAG_LIST_FIRST                 = "GETFIRSTLISTELEM"
    # Require delta validation
    FLAG_REQ_DELTA                  = "YAMLSUCKS"
    # Try to format the value as a valid input for layer-protocol
    FLAG_FORMAT_IP                  = "FORMATIPVER"

    mapping = {}

    def __init__(self, dict_tosca, dict_sol6):
        super().__init__(dict_tosca, dict_sol6)

        self.override_deltas = False
        self.run_deltas = False

        T = TOSCAv2
        S = SOL6v2

        # Generate VDU map
        vdu_map = self.generate_map(T.node_template, T.vdu_identifier)

        sw_map = self.generate_map(T.node_template, T.virt_storage_identifier)

        # This list has the VDUs the flavors are attached to
        vdu_vim_flavors = self.get_items_from_map(T.vdu_vim_flavor, vdu_map, dict_tosca,
                                                  link_list=True)

        # Set up the boot order mapping
        # [vnfd1-deployment-control-function-1-cf-boot -> 0, parent=(None),
        # vnfd1-deployment-control-function-0-cf-boot -> 0, parent=(None)]
        # topology_template.node_templates.{c1}.properties.boot_order
        # vnfd.vdu.{c1->0}.boot-order.{1-cf-boot->0}.key
        boot_map = []
        for vdu in vdu_map:
            tosca_path = MapElem.format_path(vdu, T.vdu_boot, use_value=False, )
            boot_data = get_path_value(tosca_path, self.dict_tosca, must_exist=False, no_msg=True)
            if boot_data:
                b_map = self.generate_map_from_list(boot_data, map_args={"none_key": True})
                MapElem.add_parent_mapping(b_map, vdu)
                boot_map.append(b_map)
        boot_map = flatten(boot_map)

        # *** VDU Flavors ***
        # vim_flavors = [VDU, {"get_input": FLAVOR_NAME}], so get the dicts
        vim_flavors = [x[1] for x in vdu_vim_flavors]
        vim_flavors = self.get_input_values(vim_flavors, T.inputs, dict_tosca)

        vim_flavors = [{vdu_vim_flavors[i][0]: get_dict_key(item)} for i, item in
                       enumerate(vim_flavors)]

        # We might have duplicate values in the dictionary. Use a reverse dict and get the unique
        # elements
        # Turn the resulting dict back into a list of dicts
        vim_flavors = remove_duplicates(vim_flavors, only_keys=False)
        vim_flavors_rev = reverse_dict(vim_flavors)
        vim_flavors = listify(vim_flavors)

        flavor_map = self.generate_map_from_list(vim_flavors,
                                                 map_args={"value_map": MapElem.basic_map_list(
                                                     len(vim_flavors))})

        # From the mapping      [c1 -> 0, parent=(0 -> 0, parent=(None))]
        # and the value_dict    {'VIM_FLAVOR_CF': 'c1'}
        # generate the mapping  [VIM_FLAVOR_CF -> 0, parent=(None)]
        vim_flavors_map = []
        for k, v in vim_flavors_rev.items():
            for m in flavor_map:
                if m.name == v:
                    vim_flavors_map.append(MapElem(k, m.cur_map))

        # *** End VDU Flavors ***

        # *** Connection Point mappings ***
        # Map internal connection points to their VDUs
        cps_map = self.generate_map(T.node_template, T.int_cpd_identifier,
                                    map_function=V2Map.int_cp_mapping,
                                    map_args={"vdu_map": vdu_map})
        # Filter internal connection points that are assigned to management
        mgmt_cps_map = self.generate_map(T.node_template, T.int_cpd_mgmt_identifier,
                                         map_function=V2Map.int_cp_mapping,
                                         map_args={"vdu_map": vdu_map})

        # These are not going to be correctly mapped, so get the mapping from cps_map where
        # the names are the same
        # Every int-cpd will have a virtual-link-desc field, just if it's MGMT or ORCH is the
        # difference
        mgmt_cps_map = [x for x in cps_map if any(x.name == i.name for i in mgmt_cps_map)]
        # Get the opposite set for the orch cps. Note: this can be sped up by putting both of these
        # in a single loop
        orch_cps_map = [x for x in cps_map if not any(x.name == i.name for i in mgmt_cps_map)]

        # *** End Connection Point mapping ***

        # *** Instantiation Level mapping ***
        # Get the default instantiation level, if it exists
        def_inst = get_path_value(T.def_inst_level, self.dict_tosca)
        def_inst = get_roots_from_filter(def_inst, child_key=T.def_inst_key)
        if def_inst:
            def_inst_id = T.def_inst_key
            def_inst_desc = get_path_value(T.def_inst_desc, self.dict_tosca)
        else:
            def_inst_id = None
            def_inst_desc = None
        # TODO: Handle more than the default instantiation level

        # Problem here is we need duplicate entries, since we have, for example, 2 VDUs each
        # information needs to be assigned to
        vdu_inst_level_map = self.generate_map(T.policies, T.inst_level_identifier)

        # Get the list of targets from the mappings
        target_list = []
        for elem in vdu_inst_level_map:
            temp_vdu = get_path_value(T.inst_level_targets.format(elem.name), self.dict_tosca)
            target_list.append(temp_vdu)

        # Duplicate the inst_level_map to fill the number of targets in each one
        temp_vdu_map = []
        for i, item in enumerate(target_list):
            if isinstance(item, list):
                # We need this many duplicate keys with incremented values in the inst_map
                for j in range(len(temp_vdu_map), len(item) + len(temp_vdu_map)):
                    temp_vdu_map.insert(j, vdu_inst_level_map[i].copy())
        vdu_inst_level_map = temp_vdu_map

        # Re-adjust the mapping so that it's contiguous, since duplicating values will make it not
        MapElem.ensure_map_values(vdu_inst_level_map)
        target_list = flatten(target_list)
        # Finally generate the map for setting the vdu value
        target_map = self.generate_map_from_list(target_list)

        # ** Scaling Aspect info **
        # Get all of the scaling aspects information
        # Only handle 1 for now. TODO: Handle more
        scaling_map = self.generate_map(T.policies, T.scaling_aspects_identifier)[0]
        aspects = get_path_value(T.scaling_aspect_item_list.format(scaling_map.name),
                                 self.dict_tosca)

        aspect_f_map = self.generate_map_from_list(list(aspects.keys()))
        MapElem.add_parent_mapping(aspect_f_map, scaling_map)

        # This is in a separate method because it's a dumpster fire
        deltas_mapping = self._handle_deltas(aspect_f_map)
        # It is possible for there to be no step deltas, in that case don't run them even
        # if the input is valid
        if not deltas_mapping:
            self.override_deltas = True
            self.run_deltas = False

        # *** End Instantiation Level mapping ***

        # If there is a mapping function needed, the second parameter is a list with the mapping
        # as the second parameter
        # The first parameter is always a tuple
        # This now supports the same value mapped to different locations
        self.mapping = \
            [
             # -- Metadata --
             ((T.vnf_desc_id, self.FLAG_BLANK),                 S.vnfd_id),
             ((T.vnf_provider, self.FLAG_BLANK),                S.vnfd_provider),
             ((T.vnf_product_name, self.FLAG_BLANK),            S.vnfd_product),
             ((T.vnf_software_ver, self.FLAG_BLANK),            S.vnfd_software_ver),
             ((T.vnf_desc_ver, self.FLAG_BLANK),                S.vnfd_ver),
             ((T.vnf_product_info_name, self.FLAG_BLANK),       S.vnfd_info_name),
             ((T.desc, self.FLAG_BLANK),                        S.vnfd_info_desc),
             ((T.vnf_vnfm_info, self.FLAG_BLANK),               S.vnfd_vnfm_info),
             # -- End Metadata --

             # This happens first because IDs need to be the first element, for now
             # Setting specific values at specific indexes
             # These are currently only the two virtual links and external links
             (self.set_value(S.KEY_VIRT_LINK_MGMT, S.virt_link_desc_id, 0)),
             (self.set_value(S.KEY_VIRT_LINK_ORCH, S.virt_link_desc_id, 1)),

             (self.set_value(S.KEY_EXT_CP_MGMT, S.ext_cpd_id, 0)),
             (self.set_value(S.KEY_VIRT_LINK_MGMT, S.ext_cpd_virt_link, 0)),
             (self.set_value(S.KEY_EXT_CP_ORCH, S.ext_cpd_id, 1)),
             (self.set_value(S.KEY_VIRT_LINK_ORCH, S.ext_cpd_virt_link, 1)),


             # End set values

             ((T.vdu, self.FLAG_KEY_SET_VALUE),                 [S.vdu_id, vdu_map]),
             ((T.vdu_name, self.FLAG_BLANK),                    [S.vdu_name, vdu_map]),
             ((T.vdu_desc, self.FLAG_BLANK),                    [S.vdu_desc, vdu_map]),

             # Each value is a list, but we've created a mapping that handles that, so only
             # set the first value of the list
             # We want a unique int for the key here, and we have that in the mapping, but it's
             # the sol6 mapping, so swap the tosca map to the sol6 with FLAG_USE_VALUE, then
             # set the value to the key, and pass in '{}' so the mapping is the only thing we're
             # setting. This gives a list of numbers from 0->len
             (("{}", (self.FLAG_ONLY_NUMBERS, self.FLAG_LIST_FIRST, self.FLAG_USE_VALUE,
                      self.FLAG_KEY_SET_VALUE)),
              [S.vdu_boot_key, boot_map]),
             ((T.vdu_boot, self.FLAG_LIST_FIRST),               [S.vdu_boot_value, boot_map]),

             # The first value in the map is what we want to set, so insert that into the 'key'
             (("{}", self.FLAG_KEY_SET_VALUE),                  [S.vnfd_vcd_id, vim_flavors_map]),
             ((T.vdu_virt_cpu_num, self.FLAG_ONLY_NUMBERS),     [S.vnfd_vcd_cpu_num, flavor_map]),
             ((T.vdu_virt_mem_size, self.FLAG_ONLY_NUMBERS),    [S.vnfd_vcd_mem_size, flavor_map]),

             ((T.int_cpd, self.FLAG_KEY_SET_VALUE),             [S.int_cpd_id, cps_map]),
             ((T.int_cpd_layer_prot, self.FLAG_FORMAT_IP),          [S.int_cpd_layer_prot, cps_map]),
             ((S.KEY_VIRT_LINK_MGMT, self.FLAG_KEY_SET_VALUE),  [S.int_cpd_virt_link_desc,
                                                                 mgmt_cps_map]),
             ((S.KEY_VIRT_LINK_ORCH, self.FLAG_KEY_SET_VALUE),  [S.int_cpd_virt_link_desc,
                                                                 orch_cps_map]),

             # -- Software Image --
             ((T.virt_storage, self.FLAG_KEY_SET_VALUE),        [S.sw_id, sw_map]),
             ((T.sw_name, self.FLAG_BLANK),                     [S.sw_name, sw_map]),
             ((T.sw_name, self.FLAG_BLANK),                     [S.sw_image_name_var, sw_map]),
             ((T.sw_version, self.FLAG_BLANK),                  [S.sw_version, sw_map]),
             ((T.sw_checksum, self.FLAG_BLANK),                 [S.sw_checksum, sw_map]),
             ((T.sw_container_fmt, self.FLAG_BLANK),            [S.sw_container_format, sw_map]),
             ((T.sw_disk_fmt, self.FLAG_BLANK),                 [S.sw_disk_format, sw_map]),
             ((T.sw_min_disk, self.FLAG_ONLY_NUMBERS),          [S.sw_min_disk, sw_map]),
             ((T.sw_size, self.FLAG_ONLY_NUMBERS),              [S.sw_size, sw_map]),
             ((T.sw_image_file, self.FLAG_BLANK),               [S.sw_image, sw_map]),
             # -- End Software Image --

             # -- Deployment Flavor --
             ((T.df_id, self.FLAG_BLANK),                       S.df_id),
             # Assign the default instantiation level to the first element in the array
             (self.set_value(def_inst_id, S.df_inst_level_id, 0)),
             (self.set_value(def_inst_desc, S.df_inst_level_desc, 0)),
             ((T.df_desc, self.FLAG_BLANK),                     S.df_desc),
             ((T.vdu, self.FLAG_KEY_SET_VALUE),                 [S.df_vdu_prof_id, vdu_map]),
             ((T.vdu_prof_inst_min, self.FLAG_BLANK),           [S.df_vdu_prof_inst_min, vdu_map]),
             ((T.vdu_prof_inst_max, self.FLAG_BLANK),           [S.df_vdu_prof_inst_max, vdu_map]),
             (("{}", self.FLAG_KEY_SET_VALUE),                  [S.df_inst_level_vdu_vdu,
                                                                 target_map]),
             ((T.inst_level_num_instances, self.FLAG_BLANK),    [S.df_inst_level_vdu_num,
                                                                 vdu_inst_level_map]),

             ((T.scaling_aspect_name, self.FLAG_BLANK),  [S.df_inst_scaling_aspect, aspect_f_map]),
             ((T.scaling_aspect_level, self.FLAG_BLANK), [S.df_inst_scaling_level, aspect_f_map]),

             ((T.scaling_aspect_name, self.FLAG_BLANK),  [S.df_scale_aspect_id, aspect_f_map]),
             ((T.scaling_aspect_name, self.FLAG_BLANK),  [S.df_scale_aspect_name, aspect_f_map]),
             ((T.scaling_aspect_level, self.FLAG_BLANK), [S.df_scale_aspect_max_level,
                                                          aspect_f_map]),
             ((T.scaling_aspect_desc, self.FLAG_BLANK),  [S.df_scale_aspect_desc, aspect_f_map]),
             ((T.scaling_aspect_deltas, self.FLAG_REQ_DELTA),
              [S.df_scale_aspect_deltas, aspect_f_map]),

             (("{}", (self.FLAG_REQ_DELTA, self.FLAG_KEY_SET_VALUE)),
              [S.df_scale_aspect_vdu_id, deltas_mapping]),
             ((T.scaling_aspect_deltas_num, self.FLAG_REQ_DELTA),
              [S.df_scale_aspect_vdu_num, deltas_mapping])

             # -- End Deployment Flavor --
            ]

    def set_value(self, val, path, index):
        return (val, self.FLAG_KEY_SET_VALUE), [path, [MapElem(val, index)]]

    def _handle_deltas(self, aspect_f_map):
        """
        ** WARNING: Here be bullshit **

        This whole block of code gets the delta values from tosca (if they exist, they might not)
        then, it figures out what the deltas parent functions are, and it maps the delta values to
        ints for assignability in an array
        After that, it goes and figures out what the delta's parent map is and assigns the proper
        parent map to that (from aspect_f_map).
        THEN, FINALLY, we have the finished mapping:
        
        topology_template.policies.{scaling_aspects}.properties.aspects.{session-function}
                                                                   .step_deltas ==> ['delta_1']
        step_deltas_map = [data_1 -> 0, parent=(session-function -> 0)]
        vnfd.df.scaling-aspect.{session-function->0}.vdu-delta.{delta_1->0}.id = {}
                   topology_template.policies.{scaling_aspects}.properties.deltas.{delta_1}
        
        Then (we're not done yet), we have the num_instances value, but not it's full location.
        So, just stick the value into a location that we know and can access easily.
        """

        deltas_name = KeyUtils.get_path_last(TOSCAv2.scaling_aspect_deltas)
        deltas_num = KeyUtils.get_path_last(TOSCAv2.scaling_aspect_deltas_num)
        # Get all the elements that have step_deltas
        deltas = get_roots_from_filter(self.dict_tosca, child_key=deltas_name)

        deltas_mapping = None
        if deltas:
            # Get the values of all the step_deltas, and turn them into a flat list
            all_deltas = []
            delta_links = {}
            for delta in deltas:
                func_name = get_dict_key(delta)
                all_deltas.append(delta[func_name][deltas_name])
                for item in all_deltas[-1]:
                    delta_links[item] = func_name
            all_deltas = flatten(all_deltas)

            # Get all the delta values that are children of elements in all_deltas
            delta_values = get_roots_from_filter(self.dict_tosca, child_key=deltas_num,
                                                 parent_filter=all_deltas)

            # Map the keys to ints
            deltas_mapping = self.generate_map_from_list([get_dict_key(d) for d in delta_values])
            delta_values = merge_list_of_dicts(delta_values)
            for d_m in deltas_mapping:
                # Find parent mapping and assign it to the current delta mapping
                for a_m in aspect_f_map:
                    if a_m.name == delta_links[d_m.name]:
                        MapElem.add_parent_mapping(d_m, a_m)
                        # Now place the value in delta_values into the path we have mapped
                        cur_path = MapElem.format_path(d_m, TOSCAv2.scaling_aspect_deltas_num,
                                                       use_value=False)
                        # Remove the last element in the path (num-instances)
                        cur_path = KeyUtils.remove_path_elem(cur_path, -1)
                        set_path_to(cur_path, self.dict_tosca, delta_values[d_m.name],
                                    create_missing=True)
        return deltas_mapping

    @staticmethod
    def int_cp_mapping(names, map_start, **kwargs):
        if "filtered" not in kwargs or "vdu_map" not in kwargs:
            raise KeyError("The proper arguments haven't been passed for this method")

        mapping = []
        filtered = kwargs["filtered"]
        vdu_mappings = list(kwargs["vdu_map"])
        cur_num = map_start
        last_vdu = None

        # Loop through the CP names
        for name in names:
            # Get the dict that's related to this name
            # There should only be one element in the list
            entry = [x for x in filtered if get_dict_key(x) == name].pop()

            # Get the virtual_binding for this element from the filtered list
            # Remove the beginning of the path since we aren't dealing with the entire dict here
            path_lvl = KeyUtils.remove_path_level(TOSCAv2.int_cpd_virt_binding,
                                                  TOSCAv2.node_template)
            vdu = get_path_value(path_lvl.format(name), entry)

            # We need to find the parent mapping so we can include it in the map definition
            cur_vdu_map = None
            for v_map in vdu_mappings:
                if v_map.name == vdu:
                    cur_vdu_map = v_map
                    break

            # Iterate the map number if we've seen this vdu before, otherwise start over from 0
            if last_vdu == vdu:
                cur_num += 1
            else:
                cur_num = map_start
                last_vdu = vdu

            # Build the MapElem object, this stores all the parent mappings as well
            mapping.append(MapElem(name, cur_num, cur_vdu_map))

        return mapping


class KeyUtils:
    """
    General utility methods to use on paths from this file
    
    """
    @staticmethod
    def get_path_last(path, n=1):
        """
        Get the n last elements of the path, with their separators between them
        """
        paths = path.split(".")
        if len(paths) > 0:
            return ".".join(paths[len(paths) - n:len(paths)])
        raise KeyError("Path {} is an invalid path to use in this method.".format(path))

    @staticmethod
    def remove_path_first(path, n=1):
        """ Get the string without the first n elements of the path """
        paths = path.split(".")
        if len(paths) > 0:
            return ".".join(paths[n:len(paths)])
        raise KeyError("Path {} is an invalid path to use in this method.".format(path))

    @staticmethod
    def remove_path_level(path, path_level):
        return KeyUtils.remove_path_first(path, KeyUtils.get_path_level(path_level))

    @staticmethod
    def remove_path_elem(path, elem):
        """
        Remove the given elem of the path, return the path string without that element
        """
        paths = path.split(".")
        del paths[elem]
        return ".".join(paths)

    @staticmethod
    def get_path_level(path):
        return path.count(".") + 1
