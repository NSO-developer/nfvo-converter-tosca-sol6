
def get_path_value(path, cur_dict, must_exist=True):
    """
    topology_template.node_templates.vnf.properties.descriptor_id
    Pass in a path and a dict the path applies to and get the value of the key

    This is experimental, and disabled for now.
    If map_inputs is set, the method will check to see if the final result
    is an input from TOSCA, and if so it will try to return that instead of the
    raw value.
    """
    values = path.split(".")
    cur_context = cur_dict

    for val in values:
        if isinstance(cur_context, list):
            # Check if all the elements are dicts, if so just merge them
            merge = True
            for item in cur_context:
                if not isinstance(item, dict):
                    merge = False
                    break

            if merge and len(cur_context) > 1:
                cur_context = merge_list_of_dicts(cur_context)
            else:
                cur_context = cur_context[0]

        if val in cur_context:
            cur_context = cur_context[val]
        else:
            if must_exist:
                raise KeyError("Path '{}' not found in {}".format(val, path))
            else:
                print("{} not found in {}".format(val, path))
                return False
    return cur_context


def set_path_to(path, cur_dict, value, create_missing=False, list_elem=0):
    """
    Sets the value of path inside of cur_dict to value
    If create_missing is set then it will create all the required dicts to make the assignment true

    If a list is encountered and set_all_lists is false, then the method will pick list_elem
    in the list and continue with that as the context.
    """
    values = path.split(".")
    cur_context = cur_dict
    i = 0
    while i < len(values):
        if values[i].isdigit() and not isinstance(cur_context, list):
            cur_context = [cur_context]

        # When we encounter a list, get the list_elem (default the first) and continue
        if isinstance(cur_context, list):
            # If our value is a list index
            if values[i].isdigit():
                try:
                    cur_context = cur_context[int(values[i])]
                    i += 1
                except IndexError:
                    list_insert_padding(cur_context, int(values[i]), {})
            else:
                if cur_context:
                    cur_context = cur_context[list_elem]

        else:
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
                                   .format(values[i], path))
            i += 1


def list_insert_padding(lst, index, value):
    """
    Like list.insert, excpet if the value of index is greater than the length, it will append
    blank elements until it reaches the relevant index
    :param lst:
    :param index:
    :param value:
    :return:
    """
    if len(lst) > index:
        lst.insert(index, value)
    else:
        while len(lst) < index:
            lst.append(None)
        lst.append(value)


def get_roots_from_filter(cur_dict, child_key=None, child_value=None, parent_key=None,
                          internal_call=False, agg=None):
    """
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
    if not isinstance(cur_dict, dict):
        return None

    for key, value in cur_dict.items():
        # This only searches by key and/or value
        # Base cases
        # TODO: Simplify
        if child_key and child_key == key:
            if not child_value:
                if parent_key:
                    return {parent_key: cur_dict}
                return cur_dict
            # else
            if child_value == value:
                if parent_key:
                    return {parent_key: cur_dict}
                return cur_dict

        # This is the actual recursion and aggregation bit, a list is kept and passed
        # around that only has dicts in it, and eventually it gets to the top and is returned
        # We call this in two different places, which is why it's extracted into a method
        # There is probably a better way to do this than to have another internal method, though

        # Handle if we have a list of dicts
        if isinstance(value, list):
            for i in range(len(value)):
                r = get_roots_from_filter(value[i], child_key, child_value,
                                          internal_call=True, agg=agg)
                # Only add to the results list if we have a valid output
                if r:
                    agg.append(r)
        else:
            if isinstance(value, dict):
                res = get_roots_from_filter(cur_dict[key], child_key, child_value, key,
                                            internal_call=True, agg=agg)
                if isinstance(res, dict):
                    agg.append(res)
                elif isinstance(res, list) and len(res) > 0:
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


def merge_two_dicts(x, y):
    """
    https://stackoverflow.com/questions/38987/how-to-merge-two-dictionaries-in-a-single-expression
    """
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z


def merge_list_of_dicts(lst):
    hold = None
    final = {}
    if len(lst) % 2 != 0:
        hold = lst.pop()

    for count, item in enumerate(lst):
        final = merge_two_dicts(final, item)
    if hold:
        final = merge_two_dicts(final, hold)
    return final
