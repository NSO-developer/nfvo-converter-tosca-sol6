"""
These are automatically used without having to update anything else.
The TOSCA variables are mapped to the SOL6 ones, they must have the same names.
The program does not attempt to map variables beginning with '_'
"""
from mapping_v2 import *
import logging


class PathMaping:
    _log = None

    @staticmethod
    def get_logger():
        if not PathMaping._log:
            PathMaping._log = logging.getLogger(__name__)
        return PathMaping._log

    @staticmethod
    def format_paths(variables):
        """
        Pass in the inputs variable, then create the full paths for 'tosca' and 'sol6'
        If _VAL is at the end of the variable, don't process the path, just set the variable to
        the value.
        """
        var_tosca = variables["tosca"]
        var_sol6 = variables["sol6"]
        processed_tosca = {}
        processed_sol6 = {}

        for k in var_tosca:
            if "_VAL" not in k:
                val = PathMaping.get_full_path(k, var_tosca)
            else:
                val = var_tosca[k]
            processed_tosca[k] = val

        for k in var_sol6:
            if "_VAL" not in k:
                val = PathMaping.get_full_path(k, var_sol6)
            else:
                val = var_sol6[k]
            processed_sol6[k] = val
        variables["tosca"] = processed_tosca
        variables["sol6"] = processed_sol6
        return variables

    @staticmethod
    def set_variables(cur_dict, obj, exclude=""):
        """
        This is deprecated

        Take the input from the config file, and set the variables that are identifiers here
        This must be run before the values are used
        """
        log = PathMaping.get_logger()
        key_list = V2Mapping.get_object_keys(obj, exclude=exclude)

        for k in key_list:
            var_val = "{}_VAL".format(k)
            set_val = True if var_val in cur_dict else False

            if k not in cur_dict and not set_val:
                log.error("{} does not exist in the configuration file".format(k))
            if set_val:
                val = cur_dict[var_val]
            else:
                val = PathMaping.get_full_path(k, cur_dict)

            setattr(obj, k, val)

    @staticmethod
    def get_full_path(elem, dic):
        log = PathMaping.get_logger()
        try:
            if not isinstance(dic[elem], list):
                return dic[elem]
        except KeyError:
            log.error("Could not find {} as a parent".format(elem))
            return ""

        return "{}.{}".format(PathMaping.get_full_path(dic[elem][0], dic), dic[elem][1])


class TOSCA_BASE(PathMaping):
    pass


class SOL6_BASE(PathMaping):

    """
    Second version of the definitions
    """
    _extensions_prefix               = "tailf-etsi-rel3-nfvo-vnfm-sol1-vnfd-extensions"
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
    vnfd_vcd_flavor_name            = vnfd_virt_compute_desc + "." + _extensions_prefix \
                                      + ":flavor-name-variable"
    vnfd_vcd_cpu_num                = vnfd_virt_compute_desc + ".virtual-cpu.num-virtual-cpu"
    vnfd_vcd_mem_size               = vnfd_virt_compute_desc + ".virtual-memory.size"

    # ********************************
    # ** Virtual Storage Descriptor **
    # ********************************
    vnfd_virt_storage_desc          = vnfd + ".virtual-storage-descriptor.{}"
    vnfd_virt_storage_id            = vnfd_virt_storage_desc + ".id"
    vnfd_virt_storage_type          = vnfd_virt_storage_desc + ".type-of-storage"
    VIRT_STORAGE_DEFAULT            = "root"
    vnfd_virt_storage_size          = vnfd_virt_storage_desc + ".size-of-storage"
    vnfd_virt_storage_sw_image      = vnfd_virt_storage_desc + ".sw-image-desc"

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
    df_scale_aspect_delta_det       = df_scale_aspect + ".aspect-delta-details"
    df_scale_aspect_deltas          = df_scale_aspect_delta_det + ".deltas"
    df_scale_aspect_vdu_delta       = df_scale_aspect + ".vdu-delta.{}"
    df_scale_aspect_vdu_id          = df_scale_aspect_vdu_delta + ".id"
    df_scale_aspect_vdu_num         = df_scale_aspect_vdu_delta + ".number-of-instances"

    # ****************************
    # ** Virtual/External Links **
    # ****************************
    virt_link_desc                  = vnfd + ".int-virtual-link-desc.{}"
    virt_link_desc_id               = virt_link_desc + ".id"
    virt_link_desc_protocol         = virt_link_desc + ".connectivity-type.layer-protocol"

    ext_cpd                         = vnfd + ".ext-cpd.{}"
    ext_cpd_id                      = ext_cpd + ".id"
    ext_cpd_protocol                = ext_cpd + ".layer-protocol"
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
    vdu_vs_desc                     = vdu + ".virtual-storage-desc.{}"

    # ********************************
    # ** Internal Connection Points **
    # ********************************
    int_cpd                         = vdu + ".int-cpd.{}"
    int_cpd_id                      = int_cpd + ".id"
    int_cpd_layer_prot              = int_cpd + ".layer-protocol"
    int_cpd_virt_link_desc          = int_cpd + ".int-virtual-link-desc"

    KEY_VIRT_LINK_MGMT              = "CP_MGMT"
    KEY_VIRT_LINK_MGMT_PROT         = "IPv4"
    KEY_VIRT_LINK_ORCH              = "CP_ORCH"
    KEY_VIRT_LINK_ORCH_PROT         = "IPv4"
    KEY_EXT_CP_MGMT                 = "CP_EXT_MGMT"
    KEY_EXT_CP_MGMT_PROT            = "IPv4"
    KEY_EXT_CP_ORCH                 = "CP_EXT_ORCH"
    KEY_EXT_CP_ORCH_PROT            = "IPv4"

    # *******************************
    # ** Software Image Descriptor **
    # *******************************
    sw_img_desc                     = vnfd + ".sw-image-desc.{}"
    sw_id                           = sw_img_desc + ".id"
    sw_name                         = sw_img_desc + ".name"
    sw_image_name_var               = sw_img_desc + "." + \
                                      _extensions_prefix + ":image-name-variable"
    sw_version                      = sw_img_desc + ".version"
    sw_checksum                     = sw_img_desc + ".checksum"
    sw_container_format             = sw_img_desc + ".container-format"
    sw_disk_format                  = sw_img_desc + ".disk-format"
    sw_min_disk                     = sw_img_desc + ".min-disk"
    sw_size                         = sw_img_desc + ".size"
    sw_image                        = sw_img_desc + ".image"
    sw_supp_virt_environ = ""
    sw_operating_sys = ""
    sw_min_ram = ""


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
    # Label if this is a variable output
    # This means if the value to set is an input, to set it, if it is not an input, don't set
    # anything
    FLAG_VAR                        = "THISVARIABLE"
    # Marks this as requiring a value, and if there isn't one, make it 'root'
    FLAG_TYPE_ROOT_DEF              = "MUSTBESOMETHINGORROOT"

    mapping = []

    def __init__(self, dict_tosca, dict_sol6, log=None):
        super().__init__(dict_tosca, dict_sol6, log)

    def add_map(self, cur_map):
        self.mapping.append(cur_map)
