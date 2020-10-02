"""
These are automatically used without having to update anything else.
The TOSCA variables are mapped to the SOL6 ones, they must have the same names.
The program does not attempt to map variables beginning with '_'
"""
from keys.sol6_keys import TOSCA_BASE, SOL6_BASE, V2MapBase
from mapping_v2 import MapElem
from utils.dict_utils import *
from utils.list_utils import *
from utils.key_utils import *


class TOSCA(TOSCA_BASE):
    """
    Second version of the definitions
    """

    @staticmethod
    def int_cp_mgmt(item):
        """Return if the current cp is assigned to management or not"""
        return key_exists(item, "properties{}management".format(SPLIT_CHAR)) and \
            get_path_value("properties{}management".format(SPLIT_CHAR), item[get_dict_key(item)], must_exist=False)

    @staticmethod
    def virt_filter(item):
        # Make sure that the virtual storage block we get has the {}.properties.sw_image_data field
        return key_exists(item, "properties{}sw_image_data".format(SPLIT_CHAR))

    @staticmethod
    def set_variables(cur_dict, obj, exclude="", variables=None, dict_tosca=None, cur_provider=None):
        """
        Take the input from the config file, and set the variables that are identifiers here
        This must be run before the values are used
        """
        if not cur_provider:
            cur_provider = get_path_value(V2MapBase.get_value("vnf_provider", variables["tosca"]),
                                          dict_tosca).lower()
        cur_provider = "-".join(cur_provider.split(" "))
        possible_providers = variables['providers']

        # We must have a provider mapping
        if cur_provider not in possible_providers:
            raise KeyError("Provider {} not found in possible providers {}".format(cur_provider, possible_providers))

        # Get the values for the given provider
        provider_identifiers = variables["provider_identifiers"][cur_provider]

        # Get the identifiers and assign them to the relevant locations
        # It is unlikely we will ever have sol6 identifiers
        variables["tosca"]["virt_storage_identifier"] = provider_identifiers["virtual_storage"]
        variables["tosca"]["vdu_identifier"] = provider_identifiers["vdu"]
        variables["tosca"]["int_cpd_identifier"] = provider_identifiers["int_cpd"]
        variables["tosca"]["int_cpd_mgmt_identifier"] = provider_identifiers["int_cpd_mgmt"]
        variables["tosca"]["scaling_aspects_identifier"] = provider_identifiers["scaling_aspects"]
        variables["tosca"]["scaling_deltas_identifier"] = provider_identifiers["scaling_aspects_deltas"]
        variables["tosca"]["inst_level_identifier"] = provider_identifiers["instantiation_level"]
        variables["tosca"]["security_group_identifier"] = provider_identifiers["security_group"]
        variables["tosca"]["anti_affinity_identifier"] = provider_identifiers["anti_affinity_rule"]
        variables["tosca"]["affinity_identifier"] = provider_identifiers["affinity_rule"]
        variables["tosca"]["placement_group_identifier"] = provider_identifiers["placement_group"]


class SOL6(SOL6_BASE):
    pass


class V2Map(V2MapBase):
    """

    """
    # Require delta validation
    FLAG_REQ_DELTA                  = "YAMLSUCKS"
    # Label if this is a variable output
    # This means if the value to set is an input, to set it, if it is not an input, don't set
    # anything
    FLAG_VAR                        = "THISVARIABLE"
    # Marks this as requiring a value, and if there isn't one, make it 'root'
    FLAG_TYPE_ROOT_DEF              = "MUSTBESOMETHINGORROOT"

    def __init__(self, dict_tosca, dict_sol6, variables=None):
        super().__init__(dict_tosca, dict_sol6, c_log=log, variables=variables)

        # Make the lines shorter
        add_map = self.add_map
        self.tv = self.get_tosca_value
        self.sv = self.get_sol6_value
        tv = self.tv
        sv = self.sv

        TOSCA.get_path_value = get_path_value
        TOSCA.key_exists = key_exists
        TOSCA.get_dict_key = get_dict_key

        # Generate VDU map
        vdu_map = self.generate_map(None, tv("vdu_identifier"))

        # Get all the VirtualBlockStorage elements
        sw_map = self.generate_map(None, tv("virt_storage_identifier"),
                                   field_filter=TOSCA.virt_filter)

        # Adding the first sw-image-desc name to all the VDUs
        vdu_sw_map = []
        if sw_map:
            for vdu in vdu_map:
                cur_vdu = vdu.copy()
                cur_sw = sw_map[0].copy()
                MapElem.add_parent_mapping(cur_sw, cur_vdu, fail_silent=True)
                vdu_sw_map.append(cur_sw)
        else:
            # We might have sw_image_data inside vduCompute(s)
            for vdu in vdu_map:
                cur_path = MapElem.format_path(vdu, tv("vdu_sw_image_data"), use_value=False)
                img_data = get_path_value(cur_path, self.dict_tosca, must_exist=False, no_msg=True)

                # If we actually have data here, we need to format it in such a way that
                # we can process and create a new sw-image-desc based on it
                if not img_data:
                    continue

                cur_vdu = vdu.copy()
                # This is the name we have to generate, since it doesn't exist in the yaml
                name = get_path_value(MapElem.format_path(vdu, tv("vdu_name"), use_value=False), dict_tosca,
                                      must_exist=False)
                if not name:
                    name = "GEN_"
                # Just nab the first key that has actual data
                # If this fails then something really wrong has happened
                name = "{}_{}".format(name, img_data[get_dict_key(img_data)])

                cur_sw = MapElem(name, 0)
                MapElem.add_parent_mapping(cur_sw, cur_vdu, fail_silent=True)
                # Links the vdu -> sw-image-desc
                vdu_sw_map.append(cur_sw)

                # Now we need to copy the data into a new location with the proper paths in the tosca dict
                # with the name we generated
                t_path = MapElem.format_path(MapElem(name, 0), tv("sw_image_data"), use_value=False)
                set_path_to(t_path, dict_tosca, img_data, create_missing=True)

                # Then, add a new mapping into sw_map with that name
                sw_map.append(MapElem(name, 100))

        MapElem.ensure_map_values(vdu_sw_map, 0)
        MapElem.ensure_map_values(sw_map, 0)

        # This list has the VDUs the flavors are attached to
        vdu_vim_flavors = self.get_items_from_map(tv("vdu_vim_flavor"), vdu_map, dict_tosca, must_exist=False,
                                                  link_list=True)

        # Set up the boot order mapping
        # [vnfd1-deployment-control-function-1-cf-boot -> 0, parent=(None),
        # vnfd1-deployment-control-function-0-cf-boot -> 0, parent=(None)]
        # topology_template.node_templates.{c1}.properties.boot_order
        # vnfd.vdu.{c1->0}.boot-order.{1-cf-boot->0}.key
        boot_map = []
        for vdu in vdu_map:
            tosca_path = MapElem.format_path(vdu, tv("vdu_boot"), use_value=False)
            boot_data = get_path_value(tosca_path, self.dict_tosca, must_exist=False, no_msg=True)

            if boot_data:
                b_map = self.generate_map_from_list(boot_data, map_args={"none_key": True})
                MapElem.add_parent_mapping(b_map, vdu)

                boot_map.append(b_map)
        boot_map = flatten(boot_map)

        # *** VNFD Additional Configurable Parameters ***
        # TODO: Determine if the value needs to be read from the yaml
        # Right now all this does is read an array variable from the esc toml, and if those variables
        # match with values in additional_parameters.parmeters then they are added just as a key
        conf_props = get_path_value(tv("vnf_add_parameter"), dict_tosca, must_exist=False)
        conf_props_map = []
        if conf_props:
            existing_props = []
            # Just for extra validation
            for prop in tv("ADD_PARAMS_VAL"):
                if prop in conf_props:
                    existing_props.append(prop)
            conf_props_map = self.generate_map_from_list(existing_props)

        # *** End Additional Parameters ***

        # *** VDU Flavors ***
        # vim_flavors = [VDU, {"get_input": FLAVOR_NAME}], so get the second param
        # The second parameter can be either a dict with an input, or a straight value
        vim_flavors = []
        if vdu_vim_flavors:
            vim_flavors = [x[1] for x in vdu_vim_flavors]

        # If the entry is a dict, get the value inside of it, else just use the value
        vim_flavors_read = [x[get_dict_key(x)] if isinstance(x, dict)
                            else x for x in vim_flavors]

        # Given: [({'get_input': 'VIM_FLAVOR'}, 'test vim flavor')]
        # Given [(VIM_FLAV_NAME OR {'get_input': 'VIM_FLAVOR'}, 'test vim flavor')]
        # We need to reformat this to the following:
        # [{'test vim flavor': {'description': 'flavour name'}} ]
        vim_flavors_format = []
        for v in vim_flavors_read:
            content = {'description': 'flavour name'}
            if isinstance(v, dict):
                vim_flavors_format.append({v[1]: content})
            else:
                vim_flavors_format.append({v: content})

        # Get all the inputs from the file
        tosca_inputs = get_path_value(tv("inputs"), dict_tosca, must_exist=False)
        # Only do this for the values that weren't read from the config
        # Also only check for filters if it's a dict
        vim_flavors_filt = [x for x in vim_flavors if isinstance(x, dict) and
                            x[get_dict_key(x)] not in vim_flavors_read]

        # Get the values of the inputs from the file (i.e. their names)
        vim_flavors = self.get_input_values(vim_flavors_filt, tosca_inputs, dict_tosca)

        # Concat the two lists
        vim_flavors = vim_flavors_format + vim_flavors

        # Create a list of dicts: [{vdu: vim_flavors[i]}]
        # If the values are not variables, then they won't be dicts, so just put their value
        # into the list as-is
        vim_flavors_temp = []
        for i, item in enumerate(vim_flavors):
            if isinstance(item, dict):
                to_append = get_dict_key(item)
            else:
                to_append = item
            vim_flavors_temp.append({vdu_vim_flavors[i][0]: to_append})
        vim_flavors = vim_flavors_temp
        
        # We might have duplicate values in the dictionary. Use a reverse dict and get the unique
        # elements
        # Turn the resulting dict back into a list of dicts
        vim_flavors = remove_duplicates(vim_flavors, only_keys=False)
        vim_flavors_rev = reverse_dict(vim_flavors)
        vim_flavors = listify(vim_flavors)

        flavor_map = self.generate_map_from_list(vim_flavors,
                                                 map_args={"value_map": MapElem.basic_map_list(len(vim_flavors))})

        # From the mapping      [c1 -> 0, parent=(0 -> 0, parent=(None))]
        # and the value_dict    {'VIM_FLAVOR_CF': 'c1'}
        # generate the mapping  [VIM_FLAVOR_CF -> 0, parent=(None)]
        vim_flavors_map = []
        for k, v in vim_flavors_rev.items():
            for m in flavor_map:
                if m.name == v:
                    # Add parent here so the virtual compute can access the VDU to put data in
                    vim_flavors_map.append(MapElem(k, m.cur_map, m.parent_map))

        # *** End VDU Flavors ***

        # *** Day0 Variables ***
        # Get the unique names for all the artifacts across all VDUs
        day0_map = []
        for vdu in vdu_map:
            cur_path = MapElem.format_path(vdu, tv("vdu_day0_list"), use_value=False)
            cv = get_path_value(cur_path, dict_tosca, must_exist=False)
            if not cv:
                continue

            cur_day0 = self.generate_map(cur_path, None, parent=vdu)
            for c0 in cur_day0:
                custom_id = "{}::{}".format(vdu.name, c0.name)
                # The keys aren't enough for our purposes, because each VDU can have different settings
                # so we need to create a new value that we can map later
                # We *don't* need to modify day0_map because we ensure_map_values, which means they're
                # unique references
                set_path_to(MapElem.format_path(c0, tv("vdu_day0_custom_id"), use_value=False),
                            dict_tosca, custom_id, create_missing=True)
            day0_map.append(cur_day0)

        day0_map = flatten(day0_map)
        MapElem.ensure_map_values(day0_map)
        # We need to make another mapping for assigning the values in the VDUs, since there is only 1 input required
        # vnfd;vdu;{};tailf-etsi-rel3-nfvo-vnfm:artifact
        day0_vdu_map = []

        # Now handle the variables defined in day0, which are the main bit of information
        day0_variables_map = []
        for d0 in day0_map:
            cur_path = MapElem.format_path(d0, tv("vdu_day0_variables"), use_value=False)
            cur_var_map = self.generate_map(cur_path, None, parent=d0)
            day0_variables_map.append(cur_var_map)

            # The mapping data for the VDU map
            # It's in this loop to save cycles
            vdu_d0 = d0.copy()
            vdu_d0.cur_map = None
            day0_vdu_map.append(vdu_d0)

        day0_variables_map = flatten(day0_variables_map)

        # *** End Day0 Variables ***

        # *** Connection Point mappings ***
        # Map internal connection points to their VDUs
        # Get all int connection points
        cps_map = self.generate_map(None, tv("int_cpd_identifier"), map_function=self.int_cp_mapping,
                                    map_args={"vdu_map": vdu_map})

        # Each 'virtual_link' entry is a connection to an external connection point
        # For now we are going to assume that the only relevant data is the nic name
        # TODO: Fix this, because I doubt it's correct
        int_cps = []
        mgmt_cps_map = []
        orch_cps_map = []
        icps_create_map = []
        icp_create_layer_prot = []
        ext_nics = get_path_value(tv("substitution_req"), self.dict_tosca, must_exist=False)
        if ext_nics:
            # Extract the names from the list
            ext_nics = [e[get_dict_key(e)][0] for e in ext_nics]
            # Intersection: ext_nics and cps_map
            ext_cps = [m for m in cps_map if any(nic == m.name for nic in ext_nics)]
            # Union: ext_nics and cps_map
            int_cps = [m for m in cps_map if not any(nic == m.name for nic in ext_nics)]

            # For the non-external connection points, we need to create a virtual link for them
            # They already have names in the YAML, under virtual-link, so link the CPs to those virtual
            # links, and create the links if they don't already exist
            icps_to_create = []
            for icp in int_cps:
                cur_path = MapElem.format_path(icp, tv("int_cpd_virt_link"), use_value=False)
                virt_link = get_path_value(cur_path, self.dict_tosca, must_exist=False)

                cur_path = MapElem.format_path(icp, tv("int_cpd_layer_prot"), use_value=False)
                layer_protocol = get_path_value(cur_path, self.dict_tosca, must_exist=False)
                if virt_link:
                    # Skip adding the virt_link if it already exists
                    if virt_link in icps_to_create:
                        continue
                    icps_to_create.append(virt_link)
                    # Only add the layer protocol when a new virt link gets created
                    if layer_protocol:
                        icp_create_layer_prot.append(icp.copy())

            icps_create_map = self.generate_map_from_list(icps_to_create)
            # Remove any gaps in the mapping
            MapElem.ensure_map_values(icp_create_layer_prot, start_val=0)

            # Get the NICs that are assigned to management
            # This does not take into account if they are supposed to be mapped to an ECP
            mgmt_cps_map = self.generate_map(None, tv("int_cpd_mgmt_identifier"),
                                             field_filter=TOSCA.int_cp_mgmt,
                                             map_function=self.int_cp_mapping,
                                             map_args={"vdu_map": vdu_map})

            # Intersection: ext_cps and mgmt_cps_map
            # This is the NICs that are management and should have an
            # external connection point created
            mgmt_cps_map = [m for m in ext_cps if any(x.name == m.name for x in mgmt_cps_map)]
            # Union: ext_cps and mgmt_cps_map
            # Get the non-management NICs that have external connection points
            orch_cps_map = [m for m in ext_cps if not any(x.name == m.name for x in mgmt_cps_map)]
            # Note: this can be sped up by putting both of these
            # in a single loop

        # Security group map
        # The result isn't an array, so set the top-level values to None
        security_group_map_temp = self.generate_map(None, tv("security_group_identifier"),
                                                    map_args={"none_value": True})
        security_group_map = []

        if security_group_map_temp:
            for grp in security_group_map_temp:
                cur_targets = MapElem.format_path(grp, tv("security_group_targets"),
                                                  use_value=False)

                # There can be multiple targets, so duplicate the mapping to handle that
                targets = get_path_value(cur_targets, self.dict_tosca, must_exist=False)
                if not targets:
                    break

                # We're going to handle these by having different parent maps
                # Duplicate the cur map as many times as we have targets
                for i, t in enumerate(targets):
                    # t is the current target
                    cur_sec_group = grp.copy()

                    # Get the mapping from cps_map for t
                    cur_cp_map = MapElem.get_mapping_name(cps_map, t)
                    cur_sec_group.parent_map = cur_cp_map
                    security_group_map.append(cur_sec_group)

        # *** End Connection Point mapping ***

        # *** Instantiation Level mapping ***
        # Get the default instantiation level, if it exists
        def_inst = get_path_value(tv("def_inst_level"), self.dict_tosca, must_exist=False)
        def_inst = get_roots_from_filter(def_inst, child_key=tv("def_inst_key"))
        if def_inst:
            def_inst_id = tv("def_inst_key")
            def_inst_desc = get_path_value(tv("def_inst_desc"), self.dict_tosca, must_exist=False)
        else:
            def_inst_id = None
            def_inst_desc = None

        # TODO: Handle more than the default instantiation level

        # Problem here is we need duplicate entries, since we have, for example, 2 VDUs each
        # information needs to be assigned to
        vdu_inst_level_map = self.generate_map(None, tv("inst_level_identifier"))

        # Get the list of targets from the mappings
        target_list = []
        for elem in vdu_inst_level_map:
            temp_vdu = get_path_value(tv("inst_level_targets").format(elem.name), self.dict_tosca)
            target_list.append(temp_vdu)

        # Duplicate the inst_level_map to fill the number of targets in each one
        temp_vdu_map = []
        for i, item in enumerate(target_list):
            if isinstance(item, list):
                # We need this many duplicate keys with incremented values in the inst_map
                for j in range(len(temp_vdu_map), len(item) + len(temp_vdu_map)):
                    temp_vdu_map.insert(j, vdu_inst_level_map[i].copy())
        vdu_inst_level_map = temp_vdu_map
        MapElem.add_parent_mapping(vdu_inst_level_map, MapElem(None, 0))

        # Re-adjust the mapping so that it's contiguous, since duplicating values will make it not
        MapElem.ensure_map_values(vdu_inst_level_map)
        target_list = flatten(target_list)
        # Finally generate the map for setting the vdu value
        target_map = self.generate_map_from_list(target_list)
        MapElem.add_parent_mapping(target_map, MapElem(None, 0))

        # ** Scaling Aspect info **
        # Get all of the scaling aspects information
        # Support multiple definitions of the scaling_aspect
        scaling_aspects_map = []
        scaling_deltas_map = []
        scaling_aspects_id_map = self.generate_map(None, tv("scaling_aspects_identifier"))

        for scaling_aspect_top in scaling_aspects_id_map:
            cur_path = MapElem.format_path(scaling_aspect_top, tv("scaling_aspect_item_list"), use_value=False)

            # Generate the map for the <scaling-aspect> tags
            scaling_aspects_map.append(self.generate_map(cur_path, None, parent=scaling_aspect_top))

            # Note: every scaling_aspect requires a delta, even if the id is "unknown"
            for cur_vdu_aspect in scaling_aspects_map[-1]:
                cur_path = MapElem.format_path(cur_vdu_aspect, tv("scaling_aspect_deltas"), use_value=False)
                aspect_deltas = get_path_value(cur_path, dict_tosca, must_exist=False, no_msg=True)
                # Figure out if we have a delta defined
                if not aspect_deltas:
                    # If we don't then set the value to 'unknown'
                    set_path_to(cur_path, dict_tosca, sv("df_scale_aspect_no_delta_VAL"), create_missing=True)

                scaling_deltas_map.append(self.generate_map(cur_path, None, parent=cur_vdu_aspect,
                                                            map_args={"none_key": True}))

        scaling_aspects_map = flatten(scaling_aspects_map)
        scaling_deltas_map = flatten(scaling_deltas_map)

        # **** Scaling Aspect Deltas ****
        # We are going to do the scaling aspect delta information separately for now to reduce confusion
        # So the scaling aspects bit is fine, I think it's normal and, like, not stupid.
        # This, on the other hand, is real stupid. It's a very complicated relationship between elements
        # that are at different levels of the yaml and need multiple copies of each other to deal with the
        # list of targets, because sol6 needs individual elements for each element in said list.
        #
        # Be warned when reading this, it's not simple
        scaling_aspects_deltas_map = self.generate_map(None, tv("scaling_deltas_identifier"))
        # Generate n maps, where n is len(scaling_aspects_map)
        # Dict index is scaling aspect name, then list, then each elem of list is dict with delta name and information
        deltas_dict_map = {}
        for aspect in scaling_aspects_map:
            # Each map is going to be for an individual scaling aspect
            deltas_dict_map[aspect.name] = []
        # Find the list of deltas that are part of this aspect name, and assign them to the dict index

        for aspect in deltas_dict_map.keys():
            c = get_roots_from_filter(dict_tosca, "aspect", aspect)
            for root in c:
                root = root[get_dict_key(root)]
                deltas_dict_map[aspect].append(root[KeyUtils.get_path_last(tv("deltas_list"))])

        deltas_map = []
        for i, ddm in enumerate(deltas_dict_map.keys()):
            delta_map = self.generate_map_from_list(deltas_dict_map[ddm])
            for dm in delta_map:
                # We know that for every individual mapping dm, the parent scaling-function is named ddm
                # Find that mapping in scaling_aspect_map
                cur_scaling_func = MapElem.get_mapping_name(scaling_aspects_map, ddm)
                cur_scaling_func = cur_scaling_func.copy()
                # The YAML doesn't have this third parameter, so skip it there
                cur_scaling_func.name = None
                cur_scaling_func.parent_map = scaling_aspects_deltas_map[i]
                dm.parent_map = cur_scaling_func

                # Add the scaling_aspect parent to the delta
                deltas_map.append(dm)

        # Make as many entries of each element in deltas_map as there are targets
        deltas_targets_map = []
        deltas_map_temp = []
        for dm in deltas_map:
            cur_path = MapElem.format_path(dm.parent_map, tv("deltas_targets"), use_value=False)
            cur_val = get_path_value(cur_path, dict_tosca)
            if not isinstance(cur_val, list):
                log.error("{} is expected to be a list, scaling deltas will probably not work.".format(cur_val))
                break

            for i in range(len(cur_val)):
                # Get the invididual target list elements here
                deltas_targets_map.append(MapElem(i, i, dm.parent_map))
                cdm = dm.copy()
                cdm.cur_map = i
                deltas_map_temp.append(cdm)
        deltas_map = deltas_map_temp
        # **** End Scaling Aspect Deltas ****

        # *** LCM Operations Configuration Mapping ***
        heal_map = self.generate_map(tv("vnf_lcm_heal"), None)

        # *** End LCM Operations Configuration Mapping ***

        # Affinity/Anti-Affinity Mapping
        # These are references to the placement groups, labeling them as affinity or anti-affinity
        anti_aff_map = self.generate_map(None, tv("anti_affinity_identifier"))
        anti_aff_end_map = 0
        if anti_aff_map:
            anti_aff_end_map = anti_aff_map[-1].cur_map + 1
        # Start the new map at the end of the last one so we can combine smoothly
        aff_map = self.generate_map(None, tv("affinity_identifier"), map_start=anti_aff_end_map)

        # Combine them for ease of access
        anti_aff_comb_map = anti_aff_map + aff_map
        # Reorder the values so they make sense

        # These have the VDUs
        placement_groups = self.generate_map(None, tv("placement_group_identifier"))

        # Each placement group has a parent affinity rule, find that mapping
        for rule in anti_aff_comb_map:
            # Find the target and then the mapping in placement_groups
            cur_path = MapElem.format_path(rule, tv("affinity_group_targets"), use_value=False)
            rule_target_list = get_path_value(cur_path, dict_tosca)

            if not rule_target_list or not isinstance(rule_target_list, list):
                continue
            for cur_target in rule_target_list:
                cur_place_map = MapElem.get_mapping_name(placement_groups, cur_target)
                cur_place_map.parent_map = rule

        # Get the members
        aff_vdu_map = []
        for p in placement_groups:
            cur_path = MapElem.format_path(p, tv("placement_members"), use_value=False)
            # Create duplicate mappings for each entry
            # Each member list has a vdu, and we need one entry per item in the lists
            placement_targets = get_path_value(cur_path, dict_tosca)
            if not placement_targets or not isinstance(placement_targets, list):
                continue
            # Remove the current elem's value so we skip it on mapping

            for ct in placement_targets:
                cv = MapElem.get_mapping_name(vdu_map, ct)
                c = p.copy()
                # We need the name of the policy but the mapping of the group, so
                # just replace the name because who cares
                c.name = c.parent_map.name
                c.parent_map = cv.copy()
                aff_vdu_map.append(c)

        # *** End Instantiation Level mapping ***

        # If there is a mapping function needed, the second parameter is a list with the mapping
        # as the second parameter
        # The first parameter is always a tuple
        """
                TOSCA.vnf_desc_id -> SOL6.vnfd_id
                vnfd.id = "topology_template.node_templates.vnf.properties.descriptor_id"
                
                dict_tosca = yaml
                dict_sol6 = {}
        """
        add_map(((tv("vnf_desc_id"), self.FLAG_BLANK),                 sv("vnfd_id")))
        
        # -- Metadata --

        add_map(((tv("vnf_provider"), self.FLAG_BLANK),                sv("vnfd_provider")))
        add_map(((tv("vnf_product_name"), self.FLAG_BLANK),            sv("vnfd_product")))
        add_map(((tv("vnf_software_ver"), self.FLAG_BLANK),            sv("vnfd_software_ver")))
        add_map(((tv("vnf_desc_ver"), self.FLAG_BLANK),                sv("vnfd_ver")))
        add_map(((tv("vnf_product_info_name"), self.FLAG_BLANK),       sv("vnfd_info_name")))
        add_map(((tv("desc"), self.FLAG_BLANK),                        sv("vnfd_info_desc")))
        add_map(((tv("vnf_vnfm_info"), self.FLAG_BLANK),               sv("vnfd_vnfm_info")))
        # -- End Metadata --

        # -- Set Values --
        add_map(((tv("vnf_conf_autoheal"), self.FLAG_BLANK),           sv("vnfd_config_autoheal")))
        add_map(((tv("vnf_conf_autoscale"), self.FLAG_BLANK),          sv("vnfd_config_autoscale")))
        add_map(((tv("vnf_add_param_elem"), self.FLAG_VAR),
                 [sv("vnfd_config_add_key"), conf_props_map]))

        # Create the internal virtual links specified by the YAML
        add_map((("{}", self.FLAG_KEY_SET_VALUE),
                 [sv("virt_link_desc_id"), icps_create_map]))
        add_map(((tv("int_cpd_layer_prot"), (self.FLAG_FORMAT_IP, self.FLAG_LIST_FIRST)),
                 [sv("virt_link_desc_protocol"), icp_create_layer_prot]))

        add_map(((tv("int_cpd_cidr"), (self.FLAG_VAR, self.FLAG_FAIL_SILENT)),
                 [sv("virt_link_desc_cidr"), icps_create_map]))
        add_map(((tv("int_cpd_dhcp"), (self.FLAG_VAR, self.FLAG_FAIL_SILENT)),
                 [sv("virt_link_desc_dhcp"), icps_create_map]))

        # There might or might not be a mgmt and/or orchestration external connection point
        # Create the virtual links and external connection points
        create_ext_mgmt = bool(mgmt_cps_map)
        create_ext_orch = bool(orch_cps_map)
        cur_icp = len(icps_create_map)
        cur_ecp = 0

        if create_ext_mgmt:
            add_map((self.set_value(sv("KEY_VIRT_LINK_MGMT_VAL"),
                                    sv("virt_link_desc_id"), cur_icp)))
            # For these I need a mapping of (None -> 0, parent=(val -> cur_icp))
            add_map((self.set_value(sv("KEY_VIRT_LINK_MGMT_PROT_VAL"),
                                    sv("virt_link_desc_protocol"), cur_icp, prefix_index=0)))

            add_map((self.set_value(sv("KEY_EXT_CP_MGMT_VAL"), sv("ext_cpd_id"), cur_ecp)))
            add_map((self.set_value(sv("KEY_EXT_CP_MGMT_PROT_VAL"),
                                    sv("ext_cpd_protocol"), cur_ecp)))
            add_map((self.set_value(sv("KEY_VIRT_LINK_MGMT_VAL"),
                                    sv("ext_cpd_virt_link"), cur_ecp)))
            cur_icp += 1
            cur_ecp += 1

        if create_ext_orch:
            add_map((self.set_value(sv("KEY_VIRT_LINK_ORCH_VAL"),
                                    sv("virt_link_desc_id"), cur_icp)))
            add_map((self.set_value(sv("KEY_VIRT_LINK_ORCH_PROT_VAL"),
                                    sv("virt_link_desc_protocol"), cur_icp, prefix_index=0)))

            add_map((self.set_value(sv("KEY_EXT_CP_ORCH_VAL"), sv("ext_cpd_id"), cur_ecp)))
            add_map((self.set_value(sv("KEY_EXT_CP_ORCH_PROT_VAL"),
                                    sv("ext_cpd_protocol"), cur_ecp)))
            add_map((self.set_value(sv("KEY_VIRT_LINK_ORCH_VAL"),
                                    sv("ext_cpd_virt_link"), cur_ecp)))
        # -- End Set Values --

        # -- VDU --
        add_map(((tv("vdu"), self.FLAG_KEY_SET_VALUE),                 [sv("vdu_id"), vdu_map]))
        add_map(((tv("vdu_name"), self.FLAG_BLANK),                    [sv("vdu_name"), vdu_map]))
        add_map(((tv("vdu_desc"), self.FLAG_BLANK),                    [sv("vdu_desc"), vdu_map]))

        # Each value is a list, but we've created a mapping that handles that, so only
        # set the first value of the list
        # We want a unique int for the key here, and we have that in the mapping, but it's
        # the sol6 mapping, so swap the tosca map to the sol6 with FLAG_USE_VALUE, then
        # set the value to the key, and pass in '{}' so the mapping is the only thing we're
        # setting. This gives a list of numbers from 0->len
        add_map((("{}", (self.FLAG_ONLY_NUMBERS, self.FLAG_LIST_NTH, self.FLAG_USE_VALUE,
                 self.FLAG_KEY_SET_VALUE)),             [sv("vdu_boot_key"), boot_map]))
        add_map(((tv("vdu_boot"), self.FLAG_LIST_NTH),        [sv("vdu_boot_value"), boot_map]))

        add_map(((tv("vdu_boot"), self.FLAG_LIST_NTH),        [sv("vdu_vs_desc"), boot_map]))
        add_map((("{}", self.FLAG_KEY_SET_VALUE),
                 [sv("vdu_vc_desc"), vim_flavors_map]))
        add_map(((tv("virt_storage"), self.FLAG_KEY_SET_VALUE),
                 [sv("vdu_sw_image_desc"), vdu_sw_map]))
        # -- End VDU --

        # -- Virtual Compute Descriptor --
        # The first value in the map is what we want to set, so insert that into the 'key'
        add_map((("{}", self.FLAG_KEY_SET_VALUE),
                 [sv("vnfd_vcd_id"), vim_flavors_map]))
        add_map(((tv("vdu_vim_flavor"), self.FLAG_VAR),
                 [sv("vnfd_vcd_flavor_name"), flavor_map]))
        add_map(((tv("vdu_virt_cpu_num"), self.FLAG_ONLY_NUMBERS),
                 [sv("vnfd_vcd_cpu_num"), flavor_map]))
        add_map(((tv("vdu_virt_mem_size"), (self.FLAG_UNIT_GB, self.FLAG_UNIT_FRACTIONAL)),
                 [sv("vnfd_vcd_mem_size"), flavor_map]))
        # -- End Virtual Compute Descriptor --

        # -- Internal Connction Points --
        add_map(((tv("int_cpd"), self.FLAG_KEY_SET_VALUE),
                [sv("int_cpd_id"), cps_map]))
        add_map(((tv("int_cpd_virt_link"), self.FLAG_BLANK),
                 [sv("int_cpd_virt_link_desc"), int_cps]))

        add_map(((tv("int_cpd_layer_prot"), self.FLAG_FORMAT_IP),
                 [sv("int_cpd_layer_prot"), cps_map]))
        add_map(((sv("KEY_VIRT_LINK_MGMT_VAL"), self.FLAG_KEY_SET_VALUE),
                 [sv("int_cpd_virt_link_desc"), mgmt_cps_map]))
        add_map(((sv("int_cpd_management_VAL"), self.FLAG_KEY_SET_VALUE),
                 [sv("int_cpd_management"), mgmt_cps_map]))
        add_map(((sv("KEY_VIRT_LINK_ORCH_VAL"), self.FLAG_KEY_SET_VALUE),
                 [sv("int_cpd_virt_link_desc"), orch_cps_map]))

        # Interface id, with incrementing number, use the sol6 array index
        add_map(((tv("int_cpd"), (self.FLAG_KEY_SET_VALUE,
                                  self.FLAG_USE_VALUE, self.FLAG_ONLY_NUMBERS)),
                 [sv("int_cpd_interface_id"), cps_map]))

        add_map(((tv("int_cpd_ip_allowed_addr"), (self.FLAG_VAR, self.FLAG_FAIL_SILENT)),
                [sv("int_cpd_allowed_addr"), cps_map]))

        add_map(((tv("int_cpd_ip_addr"), (self.FLAG_VAR, self.FLAG_FAIL_SILENT)),
                 [sv("int_cpd_ip_addr"), cps_map]))

        add_map(((tv("security_group_name"), (self.FLAG_VAR, self.FLAG_FAIL_SILENT)),
                 [sv("int_cpd_security"), security_group_map]))

        # -- End Internal Connection Points

        # -- Virtual Storage Descriptor --
        add_map(((tv("virt_storage"), self.FLAG_KEY_SET_VALUE),
                 [sv("vnfd_virt_storage_id"), sw_map]))
        add_map(((tv("virt_size"), self.FLAG_UNIT_GB),
                 [sv("vnfd_virt_storage_size"), sw_map]))
        add_map(((tv("virt_type"), self.FLAG_TYPE_ROOT_DEF),
                 [sv("vnfd_virt_storage_type"), sw_map]))
        add_map(((tv("virt_storage"), self.FLAG_KEY_SET_VALUE),
                 [sv("vnfd_virt_storage_sw_image"), sw_map]))

        # -- End Virtual Storage Descriptor --

        # -- Software Image --
        add_map(((tv("virt_storage"), self.FLAG_KEY_SET_VALUE),   [sv("sw_id"), sw_map]))
        add_map(((tv("virt_storage"), self.FLAG_KEY_SET_VALUE),   [sv("sw_name"), sw_map]))
        add_map(((tv("sw_name"), self.FLAG_VAR),
                 [sv("sw_image_name_var"), sw_map]))
        add_map(((tv("sw_version"), self.FLAG_BLANK),             [sv("sw_version"), sw_map]))
        add_map(((tv("sw_checksum"), self.FLAG_BLANK),            [sv("sw_checksum_hash"), sw_map]))
        # There is only one option for checksum algorithm right now, it's hardcoded in NFVO to SHA256
        for i, swm in enumerate(sw_map):
            add_map((self.set_value(sv("sw_checksum_algorithm_VAL"),
                                    MapElem.format_path(swm, sv("sw_checksum_algorithm")), i)))

        add_map(((tv("sw_container_fmt"), self.FLAG_BLANK),
                 [sv("sw_container_format"), sw_map]))
        add_map(((tv("sw_disk_fmt"), self.FLAG_BLANK),
                 [sv("sw_disk_format"), sw_map]))
        add_map(((tv("sw_min_disk"), self.FLAG_UNIT_GB),          [sv("sw_min_disk"), sw_map]))
        add_map(((tv("sw_size"), self.FLAG_UNIT_GB),              [sv("sw_size"), sw_map]))
        add_map(((tv("sw_image_file"), self.FLAG_BLANK),          [sv("sw_image"), sw_map]))
        # -- End Software Image --

        # -- Deployment Flavor --
        add_map(((tv("df_id"), self.FLAG_BLANK), sv("df_id")))
        # Assign the default instantiation level to the first element in the array
        add_map((self.set_value(def_inst_id, sv("df_inst_level_id"), 0)))
        if def_inst_desc:
            add_map((self.set_value(def_inst_desc, sv("df_inst_level_desc"), 0)))
        add_map(((tv("df_desc"), self.FLAG_BLANK), sv("df_desc")))

        add_map(((tv("vdu"), self.FLAG_KEY_SET_VALUE),
                 [sv("df_vdu_prof_id"), vdu_map]))
        add_map(((tv("vdu_prof_inst_min"), self.FLAG_BLANK),
                 [sv("df_vdu_prof_inst_min"), vdu_map]))
        add_map(((tv("vdu_prof_inst_max"), self.FLAG_BLANK),
                 [sv("df_vdu_prof_inst_max"), vdu_map]))
        add_map((("{}", self.FLAG_KEY_SET_VALUE),
                 [sv("df_inst_level_vdu_vdu"), target_map]))
        add_map(((tv("inst_level_num_instances"), self.FLAG_BLANK),
                 [sv("df_inst_level_vdu_num"), vdu_inst_level_map]))

        add_map(((tv("vnf_lcm_heal_item"), self.FLAG_KEY_SET_VALUE),
                 [sv("df_heal_param_key"), heal_map]))
        add_map(((tv("vnf_lcm_heal_item"), self.FLAG_BLANK),
                [sv("df_heal_param_value"), heal_map]))

        # Set the default instantiation level
        add_map((self.set_value(def_inst_id, sv("df_inst_level_default"), 0)))

        # -- Scaling Aspect --
        add_map(((tv("scaling_aspect_name"), self.FLAG_BLANK),
                 [sv("df_scale_aspect_id"), scaling_aspects_map]))
        add_map(((tv("scaling_aspect_name"), self.FLAG_BLANK),
                 [sv("df_scale_aspect_name"), scaling_aspects_map]))
        add_map(((tv("scaling_aspect_desc"), self.FLAG_BLANK),
                 [sv("df_scale_aspect_desc"), scaling_aspects_map]))
        add_map(((tv("scaling_aspect_level"), (self.FLAG_ONLY_NUMBERS, self.FLAG_MIN_1)),
                 [sv("df_scale_aspect_max_level"), scaling_aspects_map]))
        add_map(((tv("scaling_aspect_deltas"), self.FLAG_LIST_FIRST),
                 [sv("df_scale_aspect_deltas_id"), scaling_deltas_map]))
        # For the delta information
        add_map(((tv("deltas_num_instances"), self.FLAG_BLANK),
                 [sv("df_scale_aspect_vdu_num"), deltas_map]))
        add_map(((tv("deltas_target"), self.FLAG_BLANK),
                 [sv("df_scale_aspect_vdu_id"), deltas_targets_map]))

        # -- End Scaling Aspect

        # -- Affinity or Antiaffinity Groups --
        add_map(((tv("affinity_group"), self.FLAG_KEY_SET_VALUE),
                 [sv("df_affinity_id"), anti_aff_comb_map]))
        add_map(((tv("affinity_group_scope"), self.FLAG_FORMAT_AFF_SCOPE),
                 [sv("df_affinity_scope"), anti_aff_comb_map]))
        # Set the type based on what list they're in
        for antiaff in anti_aff_map:
            add_map((self.set_value(sv("anti_affinity_VAL"), sv("df_affinity_type"), antiaff.cur_map)))
        for aff in aff_map:
            add_map((self.set_value(sv("affinity_VAL"), sv("df_affinity_type"), aff.cur_map)))

        add_map(((tv("placement_group"), self.FLAG_KEY_SET_VALUE),
                 [sv("df_vdu_prof_aff_group_id"), aff_vdu_map]))
        # -- End Affinity or Antiaffinity Groups --
        # -- End Deployment Flavor --

        # -- Artifact --
        add_map(((tv("vdu_day0_custom_id"), self.FLAG_BLANK),
                 [sv("artifact_id"), day0_map]))
        add_map(((tv("vdu_day0_file"), self.FLAG_BLANK),
                 [sv("artifact_url"), day0_map]))
        add_map(((tv("vdu_day0"), self.FLAG_KEY_SET_VALUE),
                 [sv("artifact_dest"), day0_map]))
        add_map(((tv("vdu_day0_variable"), self.FLAG_KEY_SET_VALUE),
                 [sv("artifact_variable_id"), day0_variables_map]))
        add_map(((tv("vdu_day0_custom_id"), self.FLAG_BLANK),
                 [sv("vdu_artifact"), day0_vdu_map]))

        for i, artifact in enumerate(day0_map):
            add_map((self.set_value(sv("artifact_hash_DUMMY_VAL"), sv("artifact_hash"), i)))
            add_map((self.set_value(sv("artifact_algorithm_DUMMY_VAL"), sv("artifact_algorithm"), i)))

        # -- End Artifact --

    def int_cp_mapping(self, names, map_start, **kwargs):
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
            path_lvl = KeyUtils.remove_path_level(self.get_tosca_value("int_cpd_virt_binding"),
                                                  self.get_tosca_value("node_templates"))
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

