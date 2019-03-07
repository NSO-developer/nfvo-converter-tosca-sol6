"""
These are automatically used without having to update anything else.
The TOSCA variables are mapped to the SOL6 ones, they must have the same names.
The program does not attempt to map variables beginning with '_'
"""
from sol6_keys import TOSCA_BASE, SOL6_BASE, V2MapBase
from key_utils import KeyUtils
from mapping_v2 import MapElem
from dict_utils import *
from list_utils import *


class TOSCA(TOSCA_BASE):
    """
    Second version of the definitions
    """

    @staticmethod
    def int_cp_mgmt(item):
        """Return if the current cp is assigned to management or not"""
        return key_exists(item, "properties.management") and \
               get_path_value("properties.management", item[get_dict_key(item)], must_exist=False)

    @staticmethod
    def virt_filter(item):
        # Make sure that the virtual storage block we get has the {}.properties.sw_image_data field
        return key_exists(item, "properties.sw_image_data")


    @staticmethod
    def set_variables(cur_dict, obj, exclude="", variables=None, dict_tosca=None):
        """
        Take the input from the config file, and set the variables that are identifiers here
        This must be run before the values are used
        """
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
        variables["tosca"]["virt_storage_identifier"] = provider_identifiers["virtual_storage"]
        variables["tosca"]["vdu_identifier"] = provider_identifiers["vdu"]
        variables["tosca"]["int_cpd_identifier"] = provider_identifiers["int_cpd"]
        variables["tosca"]["int_cpd_mgmt_identifier"] = provider_identifiers["int_cpd_mgmt"]
        variables["tosca"]["scaling_aspects_identifier"] = provider_identifiers["scaling_aspects"]
        variables["tosca"]["inst_level_identifier"] = provider_identifiers["instantiation_level"]


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

    def __init__(self, dict_tosca, dict_sol6, variables=None, log=None):
        super().__init__(dict_tosca, dict_sol6, c_log=log, variables=variables)

        # Make the lines shorter
        add_map = self.add_map
        self.tv = self.get_tosca_value
        self.sv = self.get_sol6_value
        tv = self.tv
        sv = self.sv

        self.override_deltas = False
        self.run_deltas = False
        TOSCA.get_path_value = get_path_value
        TOSCA.key_exists = key_exists
        TOSCA.get_dict_key = get_dict_key

        # Generate VDU map
        vdu_map = self.generate_map(tv("node_templates"), tv("vdu_identifier"))

        sw_map = self.generate_map(tv("node_templates"), tv("virt_storage_identifier"))

        # This list has the VDUs the flavors are attached to
        vdu_vim_flavors = self.get_items_from_map(tv("vdu_vim_flavor"), vdu_map, dict_tosca,
                                                  link_list=True)

        # Set up the boot order mapping
        # [vnfd1-deployment-control-function-1-cf-boot -> 0, parent=(None),
        # vnfd1-deployment-control-function-0-cf-boot -> 0, parent=(None)]
        # topology_template.node_templates.{c1}.properties.boot_order
        # vnfd.vdu.{c1->0}.boot-order.{1-cf-boot->0}.key
        boot_map = []
        for vdu in vdu_map:
            tosca_path = MapElem.format_path(vdu, tv("vdu_boot"), use_value=False, )
            boot_data = get_path_value(tosca_path, self.dict_tosca, must_exist=False, no_msg=True)

            if boot_data:
                b_map = self.generate_map_from_list(boot_data, map_args={"none_key": True})
                MapElem.add_parent_mapping(b_map, vdu)

                boot_map.append(b_map)
        boot_map = flatten(boot_map)

        # *** VDU Flavors ***
        # vim_flavors = [VDU, {"get_input": FLAVOR_NAME}], so get the dicts
        vim_flavors = [x[1] for x in vdu_vim_flavors]
        vim_flavors = self.get_input_values(vim_flavors, tv("inputs"), dict_tosca)

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
        cps_map = self.generate_map(tv("node_templates"), tv("int_cpd_identifier"),
                                    map_function=self.int_cp_mapping,
                                    map_args={"vdu_map": vdu_map})
        # Filter internal connection points that are assigned to management
        mgmt_cps_map = self.generate_map(tv("node_templates"), tv("int_cpd_mgmt_identifier"),
                                         map_function=self.int_cp_mapping,
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
        def_inst = get_path_value(tv("def_inst_level"), self.dict_tosca, must_exist=False)
        def_inst = get_roots_from_filter(def_inst, child_key=tv("def_inst_key"))
        if def_inst:
            def_inst_id = tv("def_inst_key")
            def_inst_desc = get_path_value(tv("def_inst_desc"), self.dict_tosca)
        else:
            def_inst_id = None
            def_inst_desc = None
        # TODO: Handle more than the default instantiation level

        # Problem here is we need duplicate entries, since we have, for example, 2 VDUs each
        # information needs to be assigned to
        vdu_inst_level_map = self.generate_map(tv("policies"), tv("inst_level_identifier"))

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

        # Re-adjust the mapping so that it's contiguous, since duplicating values will make it not
        MapElem.ensure_map_values(vdu_inst_level_map)
        target_list = flatten(target_list)
        # Finally generate the map for setting the vdu value
        target_map = self.generate_map_from_list(target_list)

        # ** Scaling Aspect info **
        # Get all of the scaling aspects information
        # Only handle 1 for now. TODO: Handle more
        scaling_map = self.generate_map(tv("policies"), tv("scaling_aspects_identifier"))
        if scaling_map:
            scaling_map = scaling_map[0]
            aspects = get_path_value(tv("scaling_aspect_item_list").format(scaling_map.name),
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
        """
                TOSCA.vnf_desc_id -> SOL6.vnfd_id
                vnfd.id = "topology_template.node_templates.vnf.properties.descriptor_id"
                
                dict_tosca = yaml
                dict_sol6 = {}
        """

        self.mapping = \
            [
                # -- Metadata --
                ((tv("vnf_desc_id"), self.FLAG_BLANK),                 sv("vnfd_id")),
                ((tv("vnf_provider"), self.FLAG_BLANK),                sv("vnfd_provider")),
                ((tv("vnf_product_name"), self.FLAG_BLANK),            sv("vnfd_product")),
                ((tv("vnf_software_ver"), self.FLAG_BLANK),            sv("vnfd_software_ver")),
                ((tv("vnf_desc_ver"), self.FLAG_BLANK),                sv("vnfd_ver")),
                ((tv("vnf_product_info_name"), self.FLAG_BLANK),       sv("vnfd_info_name")),
                ((tv("desc"), self.FLAG_BLANK),                        sv("vnfd_info_desc")),
                ((tv("vnf_vnfm_info"), self.FLAG_BLANK),               sv("vnfd_vnfm_info")),
                # -- End Metadata --

                # -- Set Values --
                # This happens first because IDs need to be the first element, for now
                # Setting specific values at specific indexes
                # These are currently only the two virtual links and external links
                (self.set_value(sv("KEY_VIRT_LINK_MGMT_VAL"), sv("virt_link_desc_id"), 0)),
                (self.set_value(sv("KEY_VIRT_LINK_MGMT_PROT_VAL"), sv("virt_link_desc_protocol"), 0)),
                (self.set_value(sv("KEY_VIRT_LINK_ORCH_VAL"), sv("virt_link_desc_id"), 1)),
                (self.set_value(sv("KEY_VIRT_LINK_ORCH_PROT_VAL"), sv("virt_link_desc_protocol"), 1)),

                (self.set_value(sv("KEY_EXT_CP_MGMT_VAL"), sv("ext_cpd_id"), 0)),
                (self.set_value(sv("KEY_EXT_CP_MGMT_PROT_VAL"), sv("ext_cpd_protocol"), 0)),
                (self.set_value(sv("KEY_VIRT_LINK_MGMT_VAL"), sv("ext_cpd_virt_link"), 0)),
                (self.set_value(sv("KEY_EXT_CP_ORCH_VAL"), sv("ext_cpd_id"), 1)),
                (self.set_value(sv("KEY_EXT_CP_ORCH_PROT_VAL"), sv("ext_cpd_protocol"), 1)),
                (self.set_value(sv("KEY_VIRT_LINK_ORCH_VAL"), sv("ext_cpd_virt_link"), 1)),
                # -- End Set Values --

                # -- VDU --
                ((tv("vdu"), self.FLAG_KEY_SET_VALUE),                 [sv("vdu_id"), vdu_map]),
                ((tv("vdu_name"), self.FLAG_BLANK),                    [sv("vdu_name"), vdu_map]),
                ((tv("vdu_desc"), self.FLAG_BLANK),                    [sv("vdu_desc"), vdu_map]),

                # Each value is a list, but we've created a mapping that handles that, so only
                # set the first value of the list
                # We want a unique int for the key here, and we have that in the mapping, but it's
                # the sol6 mapping, so swap the tosca map to the sol6 with FLAG_USE_VALUE, then
                # set the value to the key, and pass in '{}' so the mapping is the only thing we're
                # setting. This gives a list of numbers from 0->len
                (("{}", (self.FLAG_ONLY_NUMBERS, self.FLAG_LIST_FIRST, self.FLAG_USE_VALUE,
                         self.FLAG_KEY_SET_VALUE)),             [sv("vdu_boot_key"), boot_map]),
                ((tv("vdu_boot"), self.FLAG_LIST_FIRST),        [sv("vdu_boot_value"), boot_map]),

                ((tv("vdu_boot"), self.FLAG_LIST_FIRST),        [sv("vdu_vs_desc"), boot_map]),
                # -- End VDU --

                # -- Virtual Compute Descriptor --
                # The first value in the map is what we want to set, so insert that into the 'key'
                (("{}", self.FLAG_KEY_SET_VALUE),
                 [sv("vnfd_vcd_id"), vim_flavors_map]),
                ((tv("vdu_vim_flavor"), self.FLAG_VAR),
                 [sv("vnfd_vcd_flavor_name"), flavor_map]),
                ((tv("vdu_virt_cpu_num"), self.FLAG_ONLY_NUMBERS),
                 [sv("vnfd_vcd_cpu_num"), flavor_map]),
                ((tv("vdu_virt_mem_size"), self.FLAG_ONLY_NUMBERS),
                 [sv("vnfd_vcd_mem_size"), flavor_map]),
                # -- End Virtual Compute Descriptor --

                # -- Internal Connction Points --
                ((tv("int_cpd"), self.FLAG_KEY_SET_VALUE),             [sv("int_cpd_id"), cps_map]),
                ((tv("int_cpd_layer_prot"), self.FLAG_FORMAT_IP),
                 [sv("int_cpd_layer_prot"), cps_map]),
                ((sv("KEY_VIRT_LINK_MGMT_VAL"), self.FLAG_KEY_SET_VALUE),
                 [sv("int_cpd_virt_link_desc"), mgmt_cps_map]),
                ((sv("KEY_VIRT_LINK_ORCH_VAL"), self.FLAG_KEY_SET_VALUE),
                 [sv("int_cpd_virt_link_desc"), orch_cps_map]),
                # -- End Internal Connection Points

                # -- Virtual Storage Descriptor --
                ((tv("virt_storage"), self.FLAG_KEY_SET_VALUE),
                 [sv("vnfd_virt_storage_id"), sw_map]),
                ((tv("virt_size"), self.FLAG_ONLY_NUMBERS),
                 [sv("vnfd_virt_storage_size"), sw_map]),
                ((tv("virt_type"), self.FLAG_TYPE_ROOT_DEF),
                 [sv("vnfd_virt_storage_type"), sw_map]),
                ((tv("virt_storage"), self.FLAG_KEY_SET_VALUE),
                 [sv("vnfd_virt_storage_sw_image"), sw_map]),
                # -- End Virtual Storage Descriptor --

                # -- Software Image --
                ((tv("virt_storage"), self.FLAG_KEY_SET_VALUE),        [sv("sw_id"), sw_map]),
                ((tv("virt_storage"), self.FLAG_KEY_SET_VALUE),        [sv("sw_name"), sw_map]),
                ((tv("sw_name"), self.FLAG_VAR),
                 [sv("sw_image_name_var"), sw_map]),
                ((tv("sw_version"), self.FLAG_BLANK),                  [sv("sw_version"), sw_map]),
                ((tv("sw_checksum"), self.FLAG_BLANK),                 [sv("sw_checksum"), sw_map]),
                ((tv("sw_container_fmt"), self.FLAG_BLANK),
                 [sv("sw_container_format"), sw_map]),
                ((tv("sw_disk_fmt"), self.FLAG_BLANK),
                 [sv("sw_disk_format"), sw_map]),
                ((tv("sw_min_disk"), self.FLAG_ONLY_NUMBERS),          [sv("sw_min_disk"), sw_map]),
                ((tv("sw_size"), self.FLAG_ONLY_NUMBERS),              [sv("sw_size"), sw_map]),
                ((tv("sw_image_file"), self.FLAG_BLANK),               [sv("sw_image"), sw_map]),
                # -- End Software Image --

                # -- Deployment Flavor --
                ((tv("df_id"), self.FLAG_BLANK),                       sv("df_id")),
                # Assign the default instantiation level to the first element in the array
                (self.set_value(def_inst_id,                sv("df_inst_level_id"), 0)),
                (self.set_value(def_inst_desc,              sv("df_inst_level_desc"), 0)),
                ((tv("df_desc"), self.FLAG_BLANK),                     sv("df_desc")),
                ((tv("vdu"), self.FLAG_KEY_SET_VALUE),
                 [sv("df_vdu_prof_id"), vdu_map]),
                ((tv("vdu_prof_inst_min"), self.FLAG_BLANK),
                 [sv("df_vdu_prof_inst_min"), vdu_map]),
                ((tv("vdu_prof_inst_max"), self.FLAG_BLANK),
                 [sv("df_vdu_prof_inst_max"), vdu_map]),
                (("{}", self.FLAG_KEY_SET_VALUE),
                 [sv("df_inst_level_vdu_vdu"), target_map]),
                ((tv("inst_level_num_instances"), self.FLAG_BLANK),
                 [sv("df_inst_level_vdu_num"), vdu_inst_level_map])

                # -- Scaling Aspect --
                #((tv("scaling_aspect_name"), self.FLAG_BLANK),
                # [sv("df_inst_scaling_aspect, aspect_f_map]),
                #((tv("scaling_aspect_level"), self.FLAG_BLANK),
                # [sv("df_inst_scaling_level, aspect_f_map]),

                #((tv("scaling_aspect_name"), self.FLAG_BLANK),
                # [sv("df_scale_aspect_id, aspect_f_map]),
                #((tv("scaling_aspect_name"), self.FLAG_BLANK),
                # [sv("df_scale_aspect_name, aspect_f_map]),
                #((tv("scaling_aspect_level"), self.FLAG_BLANK),
                # [sv("df_scale_aspect_max_level, aspect_f_map]),
                #((tv("scaling_aspect_desc"), self.FLAG_BLANK),
                # [sv("df_scale_aspect_desc, aspect_f_map]),


                #((tv("scaling_aspect_deltas"), self.FLAG_REQ_DELTA),
                #[sv("df_scale_aspect_deltas"), aspect_f_map]),

                #(("{}", (self.FLAG_REQ_DELTA, self.FLAG_KEY_SET_VALUE)),
                # [sv("df_scale_aspect_vdu_id"), deltas_mapping]),
                #((tv("scaling_aspect_deltas_num"), self.FLAG_REQ_DELTA),
                # [sv("df_scale_aspect_vdu_num"), deltas_mapping])
                # -- End Scaling Aspect

                # -- End Deployment Flavor --
            ]

    def set_value(self, val, path, index):
        return (val, self.FLAG_KEY_SET_VALUE), [path, [MapElem(val, index)]]

    def _handle_deltas(self, aspect_f_map):
        """
        ** WARNING: Here be dragons **

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

        deltas_name = KeyUtils.get_path_last(self.get_tosca_value("scaling_aspect_deltas"))
        deltas_num = KeyUtils.get_path_last(self.get_tosca_value("scaling_aspect_deltas_num"))
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
            delta_values = get_roots_from_filter(self.dict_tosca, child_key="deltas")

            # Map the keys to ints
            deltas_mapping = self.generate_map_from_list([get_dict_key(d) for d in delta_values])
            delta_values = merge_list_of_dicts(delta_values)
            for d_m in deltas_mapping:
                # Find parent mapping and assign it to the current delta mapping
                for a_m in aspect_f_map:
                    if d_m.name not in delta_links:
                        continue
                    if a_m.name == delta_links[d_m.name]:
                        MapElem.add_parent_mapping(d_m, a_m)
                        # Now place the value in delta_values into the path we have mapped
                        cur_path = MapElem.format_path(d_m, self.get_tosca_value("scaling_aspect_deltas_num"),
                                                       use_value=False)
                        # Remove the last element in the path (num-instances)
                        cur_path = KeyUtils.remove_path_elem(cur_path, -1)
                        set_path_to(cur_path, self.dict_tosca, delta_values[d_m.name],
                                    create_missing=True)
        return deltas_mapping

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

