"""
These are automatically used without having to update anything else.
The TOSCA variables are mapped to the SOL6 ones, they must have the same names.
The program does not attempt to map variables beginning with '_'
"""


class TOSCA:
    """
    The proper paths for the tosca values
    Variable names are in mostly-sol6 format. Their values are TOSCA yaml strings.
    """
    _nodes          = "topology_template.node_templates"
    _vnf            = _nodes + ".vnf"
    _properties     = _vnf + ".properties"
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
    vdu                     = _nodes + ".{}"
    vdu_cap_props           = vdu + ".capabilities.virtual_compute.properties"
    vdu_num_cpu             = vdu_cap_props + ".virtual_cpu.num_virtual_cpu"
    vdu_mem_size            = vdu_cap_props + ".virtual_memory.virtual_mem_size"
    vdu_conf_props          = vdu + ".properties.configurable_properties"
    vdu_vim_flavor          = vdu_conf_props + ".additional_vnfc_configurable_properties.vim_flavor"
    vdu_type                = "cisco.nodes.nfv.Vdu.Compute"

    vdu_profile             = vdu + ".properties.vdu_profile"
    vdu_profile_min         = vdu_profile + ".min_number_of_instances"
    vdu_profile_max         = vdu_profile + ".max_number_of_instances"

    # These also need to be formatted before use
    virtual_block_storage   = _nodes + ".{}"
    vbs_props               = virtual_block_storage + ".properties"
    vbs_size                = vbs_props + ".virtual_block_storage_data.size_of_storage"
    vbs_type                = "cisco.nodes.nfv.Vdu.VirtualBlockStorage"

    virtual_link_mapping    = _nodes + ".{}"
    _vlm_props              = virtual_link_mapping + ".properties"
    vlm_desc                = _vlm_props + ".description"
    vlm_protocols           = _vlm_props + ".connectivity_type.layer_protocols"
    vlm_type                = "tosca.nodes.nfv.VnfVirtualLink"

    group_affinity_type     = "tosca.groups.nfv.PlacementGroup"
    anti_affinity_type      = "tosca.policies.nfv.AntiAffinityRule"
    # TODO: Handle Affinity as well
    group_aff_members_key   = "members"
    policy_aff_targets_key  = "targets"
    policy_aff_type_key     = "type"
    policy_aff_scope_key    = "properties.scope"


class SOL6:
    """
    The proper paths for SOL6 yang locations
    The values are SOL6 paths
    """
    _vnfd = "vnfd"
    vnfd = _vnfd

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


class KeyUtils:
    @staticmethod
    def get_path_last(path, n=1):
        """
        Get the n last elements of the path, with their separators between them
        """
        paths = path.split(".")
        if len(paths) > 0:
            return ".".join(paths[len(paths) - n:len(paths)])
        else:
            raise KeyError("Path {} is an invalid path to use in this method.".format(path))

    @staticmethod
    def remove_path_elem(path, elem):
        """
        Remove the given elem of the path, return the path string without that element
        """
        paths = path.split(".")
        del paths[elem]
        return ".".join(paths)
