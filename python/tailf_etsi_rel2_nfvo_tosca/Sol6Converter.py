import copy
from Sol6Keys import TOSCA, SOL6, KeyUtils


class Sol6Converter:
    tosca_vnf = None
    parsed_dict = None
    vnfd = None
    template_inputs = {}
    log = None

    def __init__(self, tosca_vnf, parsed_dict, log=None):
        self.tosca_vnf = tosca_vnf
        self.parsed_dict = parsed_dict
        self.log = log

    def parse(self):
        """
        Convert the tosca_vnf to sol6 VNFD
        Currently only handles converting a single VNF to VNFD
        """
        # TODO: Handle multiple vnfds
        # First, get the vnfd specifications model
        self.vnfd = copy.deepcopy(self.parsed_dict[SOL6.vnfd])

        self._handle_one_to_one()
        # Get all of the inputs from tosca
        self.template_inputs = path_to_value(TOSCA.inputs, self.tosca_vnf)
        self._handle_virtual_compute()
        self._handle_virtual_link()

        print("End", self.vnfd)
        return self.vnfd

    def _handle_virtual_compute(self):
        """
        Get the list of vim flavor names that are in use, and find their properties
        """
        self._virtual_get_flavor_names()
        self._process_vdus()
        self._virtual_storage_set_capabilities()

        compute_descriptors = path_to_value(SOL6.virtual_comp_desc, self.vnfd)
        node_list = []

        for c in compute_descriptors:
            node_list.append(c[get_dict_key(c)])

        set_path_to(SOL6.virtual_comp_desc, self.vnfd, node_list)

    def _virtual_get_flavor_names(self):
        """
        Assume that vim flavors are always prefaced with VIM_FLAVOR
        This is a false assumption. TODO: Talk with Anu about this
        """
        flavor_names = [i for i in self.template_inputs if 'vim_flavor' in i.lower()]
        flavor_vars = {}

        # Get the flavor names & data from the inputs dict
        for flavor in flavor_names:
            flavor_vars[flavor] = self.template_inputs[flavor]

        # We need len(flavor_vars) number of duplicate 'virtual-compute-descriptors' in the
        # vnfd dict, so we will build a list
        compute_descriptors = []

        # Remove the beginning because we really don't need the full path stored inside this list
        # Loop through our data and create the paths and values in a temp dict, then append it to
        # the final list
        for name, data in flavor_vars.items():
            cur_dict = {}
            set_path_to(KeyUtils.remove_path_elem(SOL6.vcd_id, 0), cur_dict, name.lower(),
                        create_missing=True)
            set_path_to(KeyUtils.remove_path_elem(SOL6.vcd_flavor_name, 0), cur_dict, name,
                        create_missing=True)
            compute_descriptors.append(cur_dict)

        # Put the final list into the key of the dict
        set_path_to(SOL6.virtual_comp_desc, self.vnfd, compute_descriptors)

    def _process_vdus(self):
        """
        There are multiple methods that need data from VDUs, and there's no need to loop through
        them more than once, at least not right now.
        """
        # Get the information about the VDUs into a list of dicts
        vdus = get_roots_from_filter(self.tosca_vnf, child_key='type',
                                     child_value=TOSCA.vdu_type)
        virt_compute_descriptors = path_to_value(SOL6.virtual_comp_desc, self.vnfd)

        # Make a list for deployment-flavors vdu-profiles
        df_vdu_prof = []

        # First get all groups, so we can pass it in to _handle_vdu_profile later
        groups = get_roots_from_filter(self.tosca_vnf, child_key="type",
                                       child_value=TOSCA.group_affinity_type)

        anti_affinity_policies = get_roots_from_filter(self.tosca_vnf, child_key="type",
                                                       child_value=TOSCA.anti_affinity_type)

        for vdu in vdus:
            vdu_name = get_dict_key(vdu)
            # Set the virtual capabilities
            # To do this we need to match the entries from compute_descriptors to the ones in vdus
            self._virtual_compute_set_capabilities(vdu, virt_compute_descriptors)

            # Populate the configurable properties
            self._handle_config_params(vdu_name)

            # Populate the list of vdu profiles
            df_vdu_prof.append(self._populate_vdu_profile(vdu_name, groups, anti_affinity_policies))

        set_path_to(SOL6.df_vdu_profile, self.vnfd, df_vdu_prof)

        self._populate_init_affinity(anti_affinity_policies, groups)

    def _populate_init_affinity(self, anti_affinity_policies, groups):
        """
        Populate the instatiation-level (df.) anti-affinity-groups info
        We need the id, type, and scope of each group
        All the data we need is in anti_affinity_policies
        """
        # First off, get the full list of groups
        group_names = []
        for group in groups:
            group_names.append(get_dict_key(group))

        init_aff = []
        for policy in anti_affinity_policies:
            policy = policy[get_dict_key(policy)]

            # We are going to pop the group name out of this list when we've populated it
            # So if there are multiple policies that target one group, we are only going to take
            # the first one
            targets = policy[TOSCA.policy_aff_targets_key]

            try:
                for target in targets:
                    # Throws ValueError if the element is not in the list
                    group_names.remove(target)
            except ValueError:
                # Skip the outer loop if we have already found the group
                continue

            for target in targets:
                # Construct the dict of values that we need to get
                typ = policy[TOSCA.policy_aff_type_key]
                c = {KeyUtils.get_path_last(SOL6.df_affinity_group_id): target,
                     KeyUtils.get_path_last(SOL6.df_affinity_group_type):
                         SOL6.df_anti_affinity_value(typ),
                     KeyUtils.get_path_last(SOL6.df_affinity_group_scope):
                         path_to_value(TOSCA.policy_aff_scope_key, policy)}

                # Put them in the outer list
                init_aff.append(c)

        set_path_to(SOL6.df_affinity_group, self.vnfd, init_aff)

    def _populate_vdu_profile(self, vdu_name, groups, anti_aff_rules):
        """
        Populate the vdu id, min/max num of instances, then link the policies to the VDUs through
        the groups in TOSCA.
        We will then have enough information to set the affinity-or-anti-affinity-group(s) in the VDU
        and also outside of it
        :return: A dict of values for the instance
        """
        prof = {KeyUtils.get_path_last(SOL6.df_id): vdu_name,
                KeyUtils.get_path_last(SOL6.df_vdu_p_min):
                    path_to_value(TOSCA.vdu_profile_min.format(vdu_name), self.tosca_vnf),

                KeyUtils.get_path_last(SOL6.df_vdu_p_max):
                    path_to_value(TOSCA.vdu_profile_min.format(vdu_name), self.tosca_vnf)
                }

        in_groups = []
        # Find all the affinity groups that this vdu is a part of
        for g in groups:
            # The entries are all in their own dicts with a single key and entry, so get the name
            # of the group and then get the data inside of it
            name = get_dict_key(g)
            g = g[name]
            if vdu_name in g[TOSCA.group_aff_members_key]:
                in_groups.append(name)

        rules = []
        for rule in anti_aff_rules:
            name = get_dict_key(rule)
            rule = rule[name]
            targets = rule[TOSCA.policy_aff_targets_key]

            # We have the targets for each rule, now loop through them and see if any of them
            # are in our in_group, if they are add it to our rules list
            for target in targets:
                if target in in_groups:
                    rules.append(target)

        # Create the 'affinity-or-anti-affinity':'id': [ rules ] dict structure and add it to our
        # profile dict
        set_path_to(KeyUtils.get_path_last(SOL6.df_vdu_p_aff_id, 2), prof, rules,
                    create_missing=True)

        return prof

    def _virtual_compute_set_capabilities(self, vdu, compute_descriptors):
        """
        Link the flavor names with the given VDU from TOSCA, then get the number of virtual CPUs
        and memory size and place it in the relevant entry in the list at compute_descriptors
        This is the interior of a loop.
        """

        # There very strongly should only be one key in each of these dicts
        name = get_dict_key(vdu)
        # This is now the full path of the vdu
        vim_flavor = path_to_value(TOSCA.vdu_vim_flavor.format(name), self.tosca_vnf)

        if 'get_input' in vim_flavor:
            # For some reason this is wrapped in get_input, but only sometimes
            vim_flavor = vim_flavor['get_input']

        num_cpu = path_to_value(TOSCA.vdu_num_cpu.format(name), self.tosca_vnf)
        mem_size = path_to_value(TOSCA.vdu_mem_size.format(name), self.tosca_vnf)

        # Remove the 'GB' from the end and only keep the number
        mem_size = mem_size.split(" ")[0]

        # Find the compute_descriptor that matches the vim_flavor
        comp = None
        for c in compute_descriptors:
            if path_to_value(KeyUtils.remove_path_elem(SOL6.vcd_flavor_name, 0),
                             c) == vim_flavor:
                comp = c
                break

        if comp is None:
            raise ValueError("A matching compute_descriptor was not found for {}."
                             .format(vim_flavor))
        # Work with the relative path here, since we're still in a list
        set_path_to(KeyUtils.remove_path_elem(SOL6.vcd_virtual_cpu, 0),
                    comp, num_cpu, create_missing=True)
        set_path_to(KeyUtils.remove_path_elem(SOL6.vcd_virtual_memory, 0),
                    comp, mem_size, create_missing=True)

    def _handle_config_params(self, vdu_name):
        """
        Get all the additional properties and put them in a list at configurable-properties
        """
        pass

    def _virtual_storage_set_capabilities(self):
        """
        Set the virtual block storage information
        """
        vbs = get_roots_from_filter(self.tosca_vnf, child_key="type",
                                    child_value=TOSCA.vbs_type)

        res_list = []
        # There needs to be multiple entries with the same name, so we're saving this in a
        # list and handling writing it properly later
        for cur_vb in vbs:
            name = get_dict_key(cur_vb)
            storage_size = path_to_value(TOSCA.vbs_size.format(name), self.tosca_vnf)
            storage_size = storage_size.split(" ")[0]  # Remove 'GB' from the end

            dic = {KeyUtils.get_path_last(SOL6.vsd_id): name,
                   # KeyUtils.get_path_last(SOL6.vsd_type_storage): SOL6.vsd_type_storage_value,
                   KeyUtils.get_path_last(SOL6.vsd_size_storage): storage_size}

            res_list.append(dic)

        set_path_to(SOL6.virtual_storage_desc, self.vnfd, res_list)

    def _handle_virtual_link(self):
        """
        Set the data for the virtual link mapping.
        """
        links = get_roots_from_filter(self.tosca_vnf, child_key="type",
                                      child_value=TOSCA.vlm_type)
        res_list = []
        # There needs to be multiple entries with the same name, so we're saving this in a
        # list and handling writing it properly later
        for cur_link in links:
            name = get_dict_key(cur_link)
            desc = path_to_value(TOSCA.vlm_desc.format(name), self.tosca_vnf)
            protocols = path_to_value(TOSCA.vlm_protocols.format(name), self.tosca_vnf)
            protocol = protocols

            # The normal type of protocols is list, so get the first element for now
            if type(protocols) is list:
                protocol = protocols.pop()

            dic = {KeyUtils.get_path_last(SOL6.vld_id): name,
                   KeyUtils.get_path_last(SOL6.vld_desc): desc,
                   KeyUtils.get_path_last(SOL6.vld_protocol, 2): protocol}

            res_list.append(dic)

        set_path_to(SOL6.virtual_link_desc, self.vnfd, res_list, create_missing=True)

    def _handle_deployment_flavor(self):
        pass

    def _handle_connection_point(self):
        pass

    def _handle_external_connection_point(self):
        pass

    def _handle_vdu(self):
        pass

    def _handle_vnf_nfvo(self):
        pass

    def _handle_one_to_one(self):
        """
        Locate and assign the strict 1-to-1 value mappings
        """

        tosca_members = get_object_keys(TOSCA)
        sol6_members = get_object_keys(SOL6)
        # Get the intersection of the two sets of members
        valid_keys = [key for key in tosca_members if key in sol6_members]
        value_keys = [key for key in sol6_members if key + SOL6.value_key in sol6_members]

        for key in valid_keys:
            set_path_to(getattr(SOL6, key), self.vnfd,
                        path_to_value(getattr(TOSCA, key), self.tosca_vnf))

        for key in value_keys:
            set_path_to(getattr(SOL6, key), self.vnfd, getattr(SOL6, key + SOL6.value_key))


# ******* Static Methods ********
def path_to_value(path, cur_dict):
    """
    topology_template.node_templates.vnf.properties.descriptor_id
    Pass in a path and a dict the path applies to and get the value of the key
    :param path:
    :param cur_dict:
    :return:
    """
    values = path.split(".")
    cur_context = cur_dict

    for i in range(len(values)):
        if type(cur_context) is list:
            cur_context = cur_context[0]

        if values[i] in cur_context:
            cur_context = cur_context[values[i]]
        else:

            raise KeyError("Specified path/key '{}' "
                           "not found in '{}'".format(values[i], list(cur_dict.keys())[0]))

    return cur_context


def set_path_to(path, cur_dict, value, create_missing=False):
    """
    Sets the value of path inside of cur_dict to value
    If create_missing is set then it will create all the required dicts to make the assignment true
    """
    values = path.split(".")
    cur_context = cur_dict
    i = 0
    while i < len(values):
        # The current way we handle lists is to only access/set the value of the first one
        # This works fine if we aren't really using lists as lists
        if type(cur_context) is list:
            cur_context = cur_context[0]

        if values[i] in cur_context:
            if values[i] == values[-1]:
                cur_context[values[i]] = value
                break

            if not cur_context[values[i]] and create_missing:
                cur_context[values[i]] = {}
            cur_context = cur_context[values[i]]

        else:  # Enforce strict structure

            if create_missing:  # If we want to create the keys as we find they are missing
                cur_context[values[i]] = ''
                i -= 1  # Put the loop back by 1
            else:
                raise KeyError("Specified path/key {} not found in {}"
                               .format(values[i], list(cur_dict.keys())[0]))
        i += 1


def get_roots_from_filter(cur_dict, child_key=None, child_value=None, parent_key=None,
                          internal_call=False, agg=None):
    """
    Probably going to change the name of this.
    We need to be able to get root elements based on some interior condition, for example:
    
    VDU c1 has a type of 'cisco.nodes.nfv.Vdu.Compute', so we need to be able to get all the VDUs
    based on this type and value.

    This method returns a single list of the elements that meet the conditions. It performs
    aggregation along the way and returns the aggregated list at the end of the recursion.

    :return: A single list of dicts that satisfies the conditions
    """
    # Recursively search through the dict since it's a large nested dict of other dicts
    # and lists and values
    if agg is None:
        agg = []

    # Stop if we get too far in to the data and don't know how to handle it
    if not type(cur_dict) is dict:
        return None

    for key, value in cur_dict.items():
        # This only searches by key and/or value
        # Base cases
        # TODO: Simplify
        if child_key and child_key == key:
                if not child_value:
                    if parent_key:
                        return {parent_key: cur_dict}
                    else:
                        return cur_dict
                else:
                    if child_value == value:
                        if parent_key:
                            return {parent_key: cur_dict}
                        else:
                            return cur_dict

        # This is the actual recursion and aggregation bit, a list is kept and passed
        # around that only has dicts in it, and eventually it gets to the top and is returned
        # We call this in two different places, which is why it's extracted into a method
        # There is probably a better way to do this than to have another internal method, though

        # Handle if we have a list of dicts, which is very common
        if type(value) is list:
            for i in range(len(value)):
                r = get_roots_from_filter(value[i], child_key, child_value,
                                          internal_call=True, agg=agg)
                # Prevent adding to the results list if we do not have a valid output
                if r:
                    agg.append(r)
        else:
            if type(value) is dict:
                res = get_roots_from_filter(cur_dict[key], child_key, child_value, key,
                                            internal_call=True, agg=agg)

                if type(res) is dict:
                    agg.append(res)
                elif type(res) is list and len(res) > 0:
                    for e in res:
                        if e:
                            agg.append(e)

    # Keep track of if we are calling this method internally, and if we reach the endpoint where we
    # are not, that means we're at the top level of recursion, about to finish.
    # If that is the case then return our aggregated list, since we need to give it back to the
    # calling point
    if not internal_call:
        return agg


def get_dict_key(dic, n=0):
    """
    Return the first (or nth) key name from a dict
    """
    return list(dic.keys())[n]


def get_object_keys(obj):
    return [attr for attr in dir(obj) if not callable(getattr(obj, attr)) and
            not (attr.startswith("__") or attr.startswith("_"))]
