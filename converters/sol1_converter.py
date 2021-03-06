from keys.sol6_keys import *
from converters.sol1_flags import *
from keys.sol6_keys import V2MapBase
from mapping_v2 import *
import logging
log = logging.getLogger(__name__)


class Sol1Converter:

    def __init__(self, sol6_vnf, parsed_dict, variables):
        self.sol6_vnfd = sol6_vnf["data"]["etsi-nfv-descriptors:nfv"]
        self.parsed_dict = parsed_dict
        self.sol1_vnfd = {}
        self.variables = variables
        formatted_vars = PathMapping.format_paths(self.variables)

        self.va_t = formatted_vars["tosca"]
        self.va_s = formatted_vars["sol6"]
        self.mapping = []
        self.v2_map = V2Mapping(self.sol1_vnfd, self.sol6_vnfd)
        self.sol1_flags = Sol1Flags(self.sol1_vnfd, self.sol6_vnfd, variables)

        self.type_prefix = get_path_value(self.get_sol6_value("vnfd_id"), self.sol6_vnfd, must_exist=True)
        self.type_vnf = "{}_VNF".format(self.type_prefix)
        self.type_vdu = "{}_VDU_Compute".format(self.type_prefix)
        self.type_cp = "{}_VDU_CP".format(self.type_prefix)

    def convert(self):
        tv = self.get_tosca_value
        sv = self.get_sol6_value
        add_map = self.add_map

        vnfd = self.sol1_vnfd

        # -- Metadata --
        set_path_to(tv("vnf_type"), self.sol1_vnfd, self.type_vnf, create_missing=True)
        add_map(((tv("vnf_provider"), V2MapBase.FLAG_BLANK),                sv("vnfd_provider")))
        add_map(((tv("vnf_product_name"), V2MapBase.FLAG_BLANK),            sv("vnfd_product")))
        add_map(((tv("vnf_software_ver"), V2MapBase.FLAG_BLANK),            sv("vnfd_software_ver")))
        add_map(((tv("vnf_desc_ver"), V2MapBase.FLAG_BLANK),                sv("vnfd_ver")))
        add_map(((tv("vnf_product_info_name"), V2MapBase.FLAG_BLANK),       sv("vnfd_info_name")))
        add_map(((tv("desc"), V2MapBase.FLAG_BLANK),                        sv("vnfd_info_desc")))
        add_map(((tv("vnf_vnfm_info"), V2MapBase.FLAG_BLANK),               sv("vnfd_vnfm_info")))
        add_map(((tv("vnf_conf_autoheal"), V2MapBase.FLAG_BLANK),           sv("vnfd_config_autoheal")))
        add_map(((tv("vnf_conf_autoscale"), V2MapBase.FLAG_BLANK),          sv("vnfd_config_autoscale")))

        # -- End Metadata --

        # -- VDU --
        vdus = get_path_value(sv("vdus"), self.sol6_vnfd)

        vdu_ids = [vdu["id"] for vdu in vdus]
        vdu_map = self.v2_map.generate_map_from_list(vdu_ids)

        self.set_type(tv("vdu_type"), self.type_vdu, vdu_map)
        add_map(((tv("vdu_name"), V2MapBase.FLAG_BLANK),                    [sv("vdu_name"), vdu_map]))
        add_map(((tv("vdu_desc"), V2MapBase.FLAG_BLANK),                    [sv("vdu_desc"), vdu_map]))

        # Get boot order information from the kvp and put it into a useful map
        vdu_boot_order_map = []
        for vdu in vdu_map:
            boot_order = self.merge_kvp(MapElem.format_path(vdu, sv("vdu_boot_order_list")), "key")
            if len(boot_order) > 0:
                vdu_boot_order_map.append(self.v2_map.generate_map_from_list([value["value"]
                                                                              for key, value in boot_order.items()],
                                                                             map_args={"none_key": True}))
                for b in vdu_boot_order_map[-1]:
                    b.parent_map = vdu.copy()

        # This is now a list of multiple lists, so flatten that all into a single list
        vdu_boot_order_map = flatten(vdu_boot_order_map)
        add_map(((tv("vdu_boot"), (V2MapBase.FLAG_APPEND_LIST, V2MapBase.FLAG_FAIL_SILENT)),
                 [sv("vdu_boot_value"), vdu_boot_order_map]))

        # Save to variable for space reasons
        vdu_profiles = self.merge_kvp(sv("df_vdu_profile_list"), "id")
        # Generate mapping from variable
        vdu_profile_map = self.v2_map.generate_map_from_list([key for key, value in vdu_profiles.items()])
        # Finally, add the mapping itself
        add_map(((tv("vdu_prof_inst_min"), V2MapBase.FLAG_BLANK),           [sv("df_vdu_prof_inst_min"), vdu_profile_map]))
        add_map(((tv("vdu_prof_inst_max"), V2MapBase.FLAG_BLANK),           [sv("df_vdu_prof_inst_max"), vdu_profile_map]))

        # -- Connection Points --
        int_cpd_map = []
        vdu_cpd_map = []

        for vdu in vdu_map:
            int_cpds = get_path_value(MapElem.format_path(vdu, sv("int_cpd_list")), self.sol6_vnfd, must_exist=False)

            if not int_cpds:
                continue

            for i, icpd in enumerate(int_cpds):
                int_cpd_map.append(MapElem(icpd["id"], i, parent_map=vdu))
                vdu_cpd_map.append(MapElem(icpd["id"], None, parent_map=vdu))

                # Set the requirements value to be a list, which we will keep as a list,
                # since it's required to be a list for TOSCA
                set_path_to(MapElem.format_path(int_cpd_map[-1], tv("int_cpd_req"), use_value=False), self.sol1_vnfd,
                            [], create_missing=True)
            # ext_cpds = get_path_value(sv("ext_cpd"), self.sol6_vnfd)

        self.set_type(tv("int_cpd_type"), self.type_cp, int_cpd_map)
        add_map(((tv("int_cpd_layer_prot"), (V2MapBase.FLAG_FAIL_SILENT, V2MapBase.FLAG_APPEND_LIST, V2MapBase.FLAG_FORMAT_IP)),
                 [sv("int_cpd_layer_prot"), int_cpd_map]))

        add_map(((tv("int_cpd_virt_binding"), V2MapBase.FLAG_BLANK), [sv("vdu_id"), vdu_cpd_map]))
        add_map(((tv("vdu_virt_storage"), V2MapBase.FLAG_BLANK), [sv("vdu_vs_desc_list"), vdu_map]))

        # -- LCM Operations --
        # We have something like {'recovery_action': {'value': 'REBOOT_THEN_REDEPLOY'}, ...
        # So, move the internal value up one level
        lcm_opers = self.merge_kvp(sv("df_heal_param_base"), "key")
        lcm_opers = {x: lcm_opers[x]["value"] for x in lcm_opers}
        set_path_to(sv("df_lcm_heal_config"), self.sol6_vnfd, lcm_opers)

        add_map(((tv("vnf_lcm_heal"), V2MapBase.FLAG_BLANK), sv("df_lcm_heal_config")))

        # -- Deployment Flavor --
        add_map(((tv("df_id"), V2MapBase.FLAG_BLANK), sv("df_id")))

        df_vdu_profile_value = get_path_value(sv("df_inst_level_base"), self.sol6_vnfd, must_exist=False)
        df_mapping = []
        if df_vdu_profile_value:
            for i, df_inst_level in enumerate(df_vdu_profile_value):
                df_mapping.append(MapElem(df_inst_level["id"], i))

        add_map(((tv("df_desc"), V2MapBase.FLAG_LIST_FIRST), [sv("df_inst_level_desc"), df_mapping]))
        # -- End VDU --

        # -- Substitution Mappings --
        # Note: this does generate different formatted YAML than default, but the evaulation is the same
        # Ex: - virtual_link: [ c1_nic1, virtual_link]
        # Vs: - virtual_link:
        #       - c1_nic1
        #       - virtual_link
        substitution_data = [{"virtual_link": [key.name, "virtual_link"]} for key in int_cpd_map]
        set_path_to(tv("substitution_type"), self.sol1_vnfd, self.type_vnf, create_missing=True)
        set_path_to(tv("substitution_req"), self.sol1_vnfd, substitution_data, create_missing=True)
        # -- End Substitution Mappings --

        # -- Virtual Storage --
        # -- End Virtual Storage --

        # -- Artifacts --
        artifact_map = []
        for vdu in vdu_map:
            vdu_artifact = get_path_value(MapElem.format_path(vdu, sv("vdu_artifact")), self.sol6_vnfd, must_exist=False)
            if vdu_artifact:
                # Ensure everything is a list so we can flatten
                if not isinstance(vdu_artifact, list):
                    vdu_artifact = [vdu_artifact]
                for artifact in vdu_artifact:
                    artifact_map.append(MapElem(artifact, None, parent_map=vdu.copy()))

        # We know which artifact goes with which vdu, so now we need to match the artifact
        # up with the entry in the vnfd artifact list
        artifacts = get_path_value(sv("artifact_base"), self.sol6_vnfd, must_exist=False)
        if artifacts:
            for i, artifact in enumerate(artifacts):
                # To do this, loop through all the vnfd artifacts and save the index when we find a name we know
                if artifact is None:
                    continue
                for a in artifact_map:
                    if a.name == artifact["id"]:
                        a.cur_map = i
                        break

        variables = {}
        for artifact in artifact_map:
            art_vars = self.merge_kvp(MapElem.format_path(artifact, sv("artifact_variable_list")), "id")
            for cur_var in art_vars:
                art_vars[cur_var] = {"get_input": cur_var}
                variables[cur_var] = art_vars[cur_var]
            # Just set this directly into the sol1 vnfd, there's no point adding a mapping for this

            set_path_to(MapElem.format_path(artifact, tv("vdu_day0_variables"), use_value=False), self.sol1_vnfd, art_vars, create_missing=True)

        # Set the interfaces additional_parameters for the variables
        set_path_to(tv("vnf_add_parameter"), self.sol1_vnfd, variables, create_missing=True)
        add_map(((tv("vdu_day0_file"), V2MapBase.FLAG_BLANK), [sv("artifact_url"), artifact_map]))

        # -- End Artifacts --

        # -- Virtual Compute/Flavor --
        # Create map based on virtual compute entries
        # Match up vdu flavors with the virt compute entries
        virt_compute_map = []
        sol6_virt_computes = get_path_value(sv("vnfd_virt_compute_desc_base"), self.sol6_vnfd)

        for vdu in vdu_map:
            vdu_flavor = get_path_value(MapElem.format_path(vdu, sv("vdu_vc_desc_list")), self.sol6_vnfd, must_exist=False)
            if not vdu_flavor:
                continue
            vdu_flavor = vdu_flavor[0]
            for i, virt_compute in enumerate(sol6_virt_computes):
                if vdu_flavor == virt_compute["id"]:
                    virt_compute_map.append(MapElem(None, i, vdu.copy()))

        add_map(((tv("vdu_vim_flavor"), V2MapBase.FLAG_LIST_FIRST), [sv("vdu_vc_desc_list"), vdu_map]))
        add_map(((tv("vdu_virt_cpu_num"), V2MapBase.FLAG_BLANK), [sv("vnfd_vcd_cpu_num"), virt_compute_map]))
        add_map(((tv("vdu_virt_mem_size"), V2MapBase.FLAG_UNIT_GB), [sv("vnfd_vcd_mem_size"), virt_compute_map]))

        # -- End Virtual Compute/Flavor

        self.run_mapping()
        return vnfd

    # *************************
    # ** Run Mapping Methods **
    # *************************
    def run_mapping(self):
        """
        The first parameter is always a tuple, with the flags as the second parameter
        If there are multiple flags, they will be grouped in a tuple as well
        """
        for ((sol1_path, flags), map_sol6) in self.mapping:
            self.run_mapping_flags(flags, V2MapBase)
            self.run_mapping_map_needed(sol1_path, map_sol6)

    def run_mapping_flags(self, flags, flag_consts: V2MapBase):
        """
        Handle various flag operations, such as setting them to false and updating their values
        Called from run_mapping
        """
        self.sol1_flags.set_flags_false()
        self.sol1_flags.set_flags_loop(flags, flag_consts)

    def run_mapping_map_needed(self, sol1_path, map_sol6):
        """
        Determine if a mapping (list of MapElem) has been specified
        Called by run_mapping
        """
        if sol1_path is None:
            log.debug("SOL1 path is None, skipping with no error message")
            return

        log.debug("Run mapping for sol1: {} --> sol6: {}"
                  .format(sol1_path, map_sol6 if not isinstance(map_sol6, list) else map_sol6[0]))

        # Check if there is a mapping needed
        if isinstance(map_sol6, list):
            log.debug("\tMapping: {}".format(map_sol6[1]))
            self.run_mapping_islist(sol1_path, map_sol6)
        else:  # No mapping needed
            self.run_mapping_notlist(sol1_path, map_sol6)

    def run_mapping_islist(self, tosca_path, map_sol6):
        """
        What to do if there is a complex mapping needed
        Called from run_mapping_map_needed
        """
        mapping_list = map_sol6[1]  # List of MapElems
        sol6_path = map_sol6[0]
        i = -1

        for elem in mapping_list:
            i = i + 1

            # Skip this mapping element if it is None, but allow a none name to pass
            if not elem:
                continue
            if not elem.parent_map and self.sol1_flags.req_parent:
                if not self.sol1_flags.fail_silent:
                    log.warning("Parent mapping is required, but {} does not have one".format(elem))
                continue

            tosca_use_value = self.sol1_flags.tosca_use_value
            f_tosca_path = MapElem.format_path(elem, tosca_path, use_value=tosca_use_value)
            f_sol6_path = MapElem.format_path(elem, sol6_path, use_value=True)

            log.debug("Formatted paths:\n\tsol6: {} --> sol1: {}"
                      .format(f_sol6_path, f_tosca_path))

            # Handle flags for mapped values
            value = self.sol1_flags.handle_flags(f_sol6_path, f_tosca_path, i)

            # If the value doesn't exist, don't write it
            # Do write it if the value is 0, though
            write = True
            if not value:
                write = True if value is 0 else False

            if write:
                set_path_to(f_tosca_path, self.sol1_vnfd, value, create_missing=True)

    def run_mapping_notlist(self, sol1_path, map_sol6):
        """
        What to do if there is no complex mapping specified
        Called from run_mapping_map_needed
        """
        sol6_path = map_sol6
        if sol6_path is None:
            log.debug("SOL6 path is None, skipping with no error message")
            return

        # Handle the various flags for no mappings
        value = self.sol1_flags.handle_flags(sol6_path, sol1_path, 0)

        set_path_to(sol1_path, self.sol1_vnfd, value, create_missing=True)

    def merge_kvp(self, sol6_path, key):
        """
        Merge list of dicts, then reorder dicts to subdicts based on the key `key`

        Helper function for getting values with yang-based keys
        ex: "vdu-profile": [{"id": "vdu_node_1", "min-number-of-instances": 1}]
        into "vdu-profile": {"vdu_node_1": {"min-number-of-instances": 1}}

        :return: A merged dict
        """
        # Get the values
        data = get_path_value(sol6_path, self.sol6_vnfd, must_exist=False, )
        result = {}

        if not data:
            return result

        for data_dict in data:
            # Make sure key exists, skip if it doesn't
            if key not in data_dict:
                continue
            # Get what is going to become out dict key
            key_val = str(data_dict[key])

            # There might be a case where there are duplicate entries here
            # It *shouldn't* happen, but it's possible and it could give strange results
            if key_val in result:
                log.warning("merge_kvp: key_val '{}' already exists in result with contents: '{}'".format(key_val, result[key_val]))

            del data_dict[key]
            # Now move the contents (minus the key: key_val pair) into the new
            # dict
            result[key_val] = data_dict

        return result

    def add_map(self, cur_map):
        self.mapping.append(cur_map)

    def set_type(self, path, type_val, parent_map):
        """
        Sets the type value for a given path to `type_val`
        This is a helper function because the mapping algorithm I have is frustrating to
        set static values with changing parents.

        Example use:
            vdu_node_1:
                type: `type_val`
            vdu_node_2:
                type: `type_val`
        """
        type_map = [MapElem("type", None) for _ in range(len(parent_map))]
        for i, val in enumerate(parent_map):
            type_map[i].parent_map = parent_map[i]

        self.add_map(((path, V2MapBase.FLAG_KEY_SET_VALUE), [type_val, type_map]))

    def get_tosca_value(self, value):
        return V2MapBase.get_value(value, self.va_t, "tosca")

    def get_sol6_value(self, value):
        return V2MapBase.get_value(value, self.va_s, "sol6")

    @staticmethod
    def set_value(val, path, index, prefix_value=None, prefix_index=None):
        """
        TODO: Note: this does not work for sol1 yet
        Wrapper to more easily set a values when applying mappings
        """
        _mapping = MapElem(val, index)
        if prefix_value is not None or prefix_index is not None:
            _mapping = MapElem(prefix_value, prefix_index, parent_map=_mapping)
        return (val, V2MapBase.FLAG_KEY_SET_VALUE), [path, [_mapping]]
