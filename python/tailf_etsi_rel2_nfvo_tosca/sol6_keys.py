"""
These are automatically used without having to update anything else.
The TOSCA variables are mapped to the SOL6 ones, they must have the same names.
The program does not attempt to map variables beginning with '_'
"""
from mapping_v2 import V2Mapping

class TOSCA:
    """
    The proper paths for the tosca values
    Variable names are in mostly-sol6 format. Their values are TOSCA yaml strings.
    """
    _top            = "topology_template"
    _nodes          = _top + ".node_templates"
    _vnf            = _nodes + ".vnf"
    _properties     = _vnf + ".properties"
    _policies       = "tosca.policies"
    _nfv_policies   = _policies + ".nvf"
    from_input      = "get_input"
    # --------------------------------

    id                              = _properties + ".descriptor_id"
    provider                        = _properties + ".provider"
    product_name                    = _properties + ".product_name"
    software_version                = _properties + ".software_version"
    version                         = _properties + ".descriptor_version"
    product_info_name               = _properties + ".product_info_name"
    # product_info_description        = _properties + ".product_info_description"
    vnfm_info                       = _properties + ".vnfm_info"
    # --------------------------------
    # Deployment Flavor
    df_id                           = _properties + ".flavour_id"
    df_desc                         = _properties + ".flavour_description"

    # --------------------------------
    # Non-mapped variables
    inputs = "topology_template.inputs"

    # These all need to be formatted with the proper node before use
    vdu                         = _nodes + ".{}"
    vdu_cap_props               = vdu + ".capabilities.virtual_compute.properties"
    vdu_num_cpu                 = vdu_cap_props + ".virtual_cpu.num_virtual_cpu"
    vdu_mem_size                = vdu_cap_props + ".virtual_memory.virtual_mem_size"
    vdu_conf_props              = vdu + ".properties.configurable_properties"
    vdu_vim_flavor              = vdu_conf_props + ".additional_vnfc_configurable_properties" \
                                                   ".vim_flavor"
    vdu_type                    = "cisco.nodes.nfv.Vdu.Compute"

    vdu_profile                 = vdu + ".properties.vdu_profile"
    vdu_profile_min             = vdu_profile + ".min_number_of_instances"
    vdu_profile_max             = vdu_profile + ".max_number_of_instances"

    # These also need to be formatted before use
    virtual_block_storage       = _nodes + ".{}"
    vbs_props                   = virtual_block_storage + ".properties"
    vbs_size                    = vbs_props + ".virtual_block_storage_data.size_of_storage"
    vbs_type                    = "cisco.nodes.nfv.Vdu.VirtualBlockStorage"

    virtual_link_mapping        = _nodes + ".{}"
    _vlm_props                  = virtual_link_mapping + ".properties"
    vlm_desc                    = _vlm_props + ".description"
    vlm_protocols               = _vlm_props + ".connectivity_type.layer_protocols"
    vlm_type                    = "tosca.nodes.nfv.VnfVirtualLink"

    _instan_level               = "{}"
    _instan_level_properties    = _instan_level + ".properties"
    instan_level_nfv            = "{}.properties.levels"
    instan_level_nfv_desc       = instan_level_nfv + ".{}.description"
    instan_levels               = _instan_level_properties + ".levels"
    instan_level_num            = instan_levels + ".{}.number_of_instances"
    instan_level_targets        = _instan_level + ".targets"

    scaling_aspects             = "{}.properties.aspects"
    scaling_aspect              = scaling_aspects + ".{}"
    scaling_aspect_desc         = scaling_aspect + ".description"
    scaling_aspect_max_level    = scaling_aspect + ".max_scale_level"

    instan_level_type           = _nfv_policies + ".VduInstantiationLevels"
    instan_level_nfv_type       = _nfv_policies + ".InstantiationLevels"
    scaling_aspect_type         = _nfv_policies + ".ScalingAspects"
    anti_affinity_type          = _nfv_policies + ".AntiAffinityRule"
    sub_link_types              = ["virtual_link"]

    substitution_mappings       = _top + ".substitution_mappings.requirements"
    connection_point            = _nodes + ".{}"
    cp_properties               = connection_point + ".properties"
    cp_management               = cp_properties + ".management"
    cp_req                      = connection_point + ".requirements"
    cp_virt_binding             = cp_req + ".virtual_binding"
    cp_virt_link                = cp_req + ".virtual_link"
    cp_virt_link_id_key         = "id"
    cp_virt_link_desc_key       = "id"

    group_affinity_type         = "tosca.groups.nfv.PlacementGroup"
    # TODO: Handle Affinity as well
    group_aff_members_key       = "members"
    policy_aff_targets_key      = "targets"
    policy_aff_type_key         = "type"
    policy_aff_scope_key        = "properties.scope"
    cp_link_key                 = "link_type"



class SOL6:
    """
    The proper paths for SOL6 yang locations
    The values are SOL6 paths
    """
    _vnfd                           = "vnfd"
    vnfd                            = _vnfd
    # We build the VDUs out of place, then put in at the end, so we don't need the full path
    _vdu                            = "{}"

    # value_key is for if we have a default value we want to assign, the program can handle
    # assigning it automatically for basic keys
    # The variable must be postfixed with the value of 'value_key'
    value_key = "_VAL"
    # --------------------------------
    id                              = _vnfd + ".id"
    provider                        = _vnfd + ".provider"
    product_name                    = _vnfd + ".product-name"
    software_version                = _vnfd + ".software-version"
    version                         = _vnfd + ".version"
    product_info_name               = _vnfd + ".product-info-name"
    product_info_description        = _vnfd + ".product-info-description"
    vnfm_info                       = _vnfd + ".vnfm-info"
    # --------------------------------
    # Deployment Flavor
    _deployment_flavor               = _vnfd + ".df"
    df_id                            = _deployment_flavor + ".id"
    df_desc                          = _deployment_flavor + ".description"
    df_affinity_group                = _deployment_flavor + ".affinity-or-anti-affinity-group"
    df_affinity_group_id             = df_affinity_group + ".id"
    df_affinity_group_type           = df_affinity_group + ".type"
    df_affinity_group_scope          = df_affinity_group + ".scope"

    # VDU profiles are a list and will be built then placed in
    df_vdu_profile                   = _deployment_flavor + ".vdu-profile"
    df_vdu_p_id                      = df_vdu_profile + ".id"
    df_vdu_p_min                     = df_vdu_profile + ".min-number-of-instances"
    df_vdu_p_max                     = df_vdu_profile + ".max-number-of-instances"

    df_vdu_p_affinity_group          = df_vdu_profile + ".affinity-or-anti-affinity-group"
    df_vdu_p_aff_id                  = df_vdu_p_affinity_group + ".id"

    df_inst_level                    = _deployment_flavor + ".instantiation-level"
    _df_inst_vdu_level               = df_inst_level + ".vdu-level"
    df_inst_level_id                 = df_inst_level + ".id"
    df_inst_level_desc               = df_inst_level + ".description"
    df_inst_level_vdu                = _df_inst_vdu_level + ".vdu"
    df_inst_level_num                = _df_inst_vdu_level + ".number-of-instances"
    df_inst_scale_info               = df_inst_level + ".scaling-info"
    df_inst_scale_aspect             = df_inst_scale_info + ".aspect"
    df_inst_scale_level              = df_inst_scale_info + ".scale-level"

    df_scaling_aspect                = _deployment_flavor + ".scaling-aspect"
    df_scaling_id                    = df_scaling_aspect + ".id"
    df_scaling_name                  = df_scaling_aspect + ".name"
    df_scaling_desc                  = df_scaling_aspect + ".description"
    df_scaling_max_scale             = df_scaling_aspect + ".max-scale-level"

    @staticmethod
    def df_anti_affinity_value(x):
        return "anti-affinity" if x == TOSCA.anti_affinity_type else "affinity"

    # --------------------------------

    inst_def_level                   = _deployment_flavor + ".default-instantiation-level"
    inst_def_level_VAL               = "default"

    # --------------------------------
    # Non-mapped variables
    # ** Virtual Compute Descriptors **
    # Note: these are relative paths, as they are built out of place, then put into the dict later
    virtual_comp_desc               = _vnfd + ".virtual-compute-descriptor"
    vcd_id                          = virtual_comp_desc + ".id"
    vcd_flavor_name                 = virtual_comp_desc + ".flavor-name-variable"
    flavor_name_key                 = "flavor-name"
    vcd_virtual_memory              = virtual_comp_desc + ".virtual-memory.size"
    vcd_virtual_cpu                 = virtual_comp_desc + ".virtual-cpu.num-virtual-cpus"

    virtual_storage_desc            = _vnfd + ".virtual-storage-descriptor"
    vsd_id                          = virtual_storage_desc + ".id"
    vsd_type_storage                = virtual_storage_desc + ".type-of-storage"
    vsd_type_storage_value          = "lvm"  # This can't be read from the yaml at this point
    vsd_size_storage                = virtual_storage_desc + ".size-of-storage"

    virtual_link_desc               = _vnfd + ".virtual-link-descriptor"
    vld_id                          = virtual_link_desc + ".id"
    vld_desc                        = virtual_link_desc + ".description"
    vld_protocol                    = virtual_link_desc + ".connectivity-type.layer-protocol"

    ext_cp                          = _vnfd + ".ext-cpd"
    ext_cp_id                       = ext_cp + ".id"
    ext_cp_int_cp                   = ext_cp + ".int-virtual-link-desc"
    ext_cp_layer_protocol           = ext_cp + ".layer_protocol"
    ext_cp_layer_protocol_value     = "etsi-nfv:Ethernet"

    int_cp                          = _vdu + ".int-cpd"
    int_cp_id                       = int_cp + ".id"
    int_cp_link_desc                = int_cp + ".int-virtual-link-desc"

    ext_cp_mgmt_id                  = "VIM_NETWORK_MANAGEMENT"
    ext_cp_orch_id                  = "VIM_NETWORK_ORCHESTRATION"

    # -- Internal --
    cp_mgmt_key                 = "vim_management"
    cp_vim_orch_key             = "vim_orchestration"


class TOSCAv2:
    """
    Second version of the definitions
    """
    node_template                   = "topology_template.node_template"

    vdu_name                        = node_template + ".{}.properties.name"
    vdu_identifier                  = ["type", "cisco.nodes.nfv.Vdu.Compute"]


class SOL6v2:
    """
    Second version of the definitions
    """
    vnfd                            = "vnfd"
    vdus                            = vnfd + ".vdu"
    vdu_name                        = vdus + ".{}.name"


class V2Map(V2Mapping):
    """

    """

    def __init__(self, dict_tosca, dict_sol6):
        super().__init__(dict_tosca, dict_sol6)

        T = TOSCAv2
        S = SOL6v2
        # Generate VDU map
        vdu_map = self.generate_map(T.vdu_name, T.vdu_identifier[0], T.vdu_identifier[1])
        print("vdu map", vdu_map)


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
