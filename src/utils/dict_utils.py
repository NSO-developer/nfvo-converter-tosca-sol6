import logging
log = logging.getLogger(__name__)

SPLIT_CHAR = ";"


def get_path_value(path, cur_dict, must_exist=True, ensure_dict=False, no_msg=False):
    """
    topology_template.node_templates.vnf.properties.descriptor_id
    Pass in a path and a dict the path applies to and get the value of the key
    """
    values = path.split(SPLIT_CHAR)
    cur_context = cur_dict

    for val in values:
        if val.isdigit() and not isinstance(cur_context, list):
            cur_context = [cur_context]

        if isinstance(cur_context, list):
            if not val.isdigit():
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

        if cur_context is None:
            return _path_val_existant(must_exist, no_msg, val, path)

        if val.isdigit():
            try:
                cur_context = cur_context[int(val)]
            except IndexError:
                if must_exist:
                    raise
                return False
        elif val in cur_context:
            cur_context = cur_context[val]
        else:
            return _path_val_existant(must_exist, no_msg, val, path)

    if ensure_dict and isinstance(cur_context, list):
        # Merge the list into a dict
        return merge_list_of_dicts(cur_context)

    return cur_context


def _path_val_existant(must_exist, no_msg, val, path):
    if must_exist:
        raise KeyError("Path '{}' not found in {}".format(val, path))
    else:
        if not no_msg:
            log.warning("{} not found in {}".format(val, path))
        return False


def set_path_to(path, cur_dict, value, create_missing=False, list_elem=0):
    """
    Sets the value of path inside of cur_dict to value
    If create_missing is set then it will create all the required dicts to make the assignment true

    If a list is encountered and the current value is not a number, then the method will
    pick list_elem in the list and continue with that as the context.
    """
    values = path.split(SPLIT_CHAR)
    cur_context = cur_dict
    i = 0
    while i < len(values):
        if values[i].isdigit() and not isinstance(cur_context, list):
            # This does not convert the entry in the dict into a list, just the current value
            cur_context = [cur_context]
            # So, we need to set the new value explicitly
            # Concat the paths up to this point into a full path
            path_to_set = SPLIT_CHAR.join(values[0:i])
            # Use that path to recurse and set the value that we're about to work on in here
            # This will update the dict in our current method, because of how python works
            set_path_to(path_to_set, cur_dict, cur_context, create_missing=True)

        # When we encounter a list, get the list_elem (default the first) and continue
        if isinstance(cur_context, list):
            # If our value is a list index
            if values[i].isdigit():
                if i == len(values) - 1:
                    try:
                        cur_context[int(values[i])] = value
                    except IndexError:
                        list_insert_padding(cur_context, int(values[i]), value)
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
                    # Look ahead and see if we're going to be using this as a list next iteration
                    # If so, make it a list, otherwise make it a dict
                    if values[i+1].isdigit():
                        cur_context[values[i]] = []
                    else:
                        # Make sure we're not deleting an empty list
                        # This didn't happen for sol1->sol6, but 6->1 it can
                        if isinstance(cur_context[values[i]], list):
                            cur_context[values[i]] = [{}]
                        else:
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
                          internal_call=False, agg=None, user_filter=None, parent_filter=None):
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
        # Handling only child_value specified
        if child_value:
            try:
                # We'll hit a type error when trying to iterate over non-iterables
                # Just ignore it if that's the case
                if child_value == value or child_value in value:
                    if not child_key:
                        if parent_key:
                            return {parent_key: cur_dict}
                        return cur_dict
            except TypeError:
                pass

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
        if user_filter:
            kept = []
            for a in agg:
                if user_filter(a):
                    kept.append(a)
            agg = kept
        # parent_filter is a list of acceptable values for the parent key
        if parent_filter:
            agg = [d for d in agg if get_dict_key(d) in parent_filter]
        return agg


def get_path_from_filter(cur_item, child_key, child_value):
    """
    Find the first key:value pair that matches and return the path
    """
    # Recursively search through the dict since it's a large nested dict of other dicts
    # and lists and values

    # We need to handle looping over dicts or lists
    if isinstance(cur_item, dict):
        item_iterator = cur_item.items()
    elif isinstance(cur_item, list):
        item_iterator = enumerate(cur_item)
    else:
        return None

    for k, v in item_iterator:
        if k == child_key:
            if v == child_value:
                return k

        recurse = get_path_from_filter(v, child_key, child_value)
        if recurse:
            return "{}.{}".format(k, recurse)


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
        hold = lst[-1]

    for count, item in enumerate(lst):
        if not isinstance(item, dict):
            return lst
        final = merge_two_dicts(final, item)
    if hold:
        final = merge_two_dicts(final, hold)
    return final


def remove_empty_from_dict(d):
    def _handle_zero(val):
        """
        Python treats 0s as False. So return True if we want to keep it
        We also want to be able to write false values
        I'm starting to think this method isn't really worth it
        """
        if val is 0 or val is False:
            return True
        return val

    if type(d) is dict:
        return dict((k, remove_empty_from_dict(v)) for k, v in d.items() if _handle_zero(v)
                    and _handle_zero(remove_empty_from_dict(v)))
    elif type(d) is list:
        if d is [None]:  # Handle this stupid case, where we want to actually output this
            return d
        return [remove_empty_from_dict(v) for v in d if _handle_zero(v) and
                _handle_zero(remove_empty_from_dict(v))]
    else:
        return d


def key_exists(item, path, strip_first=True):
    try:
        if strip_first:
            item = item[get_dict_key(item)]
        paths = path.split(SPLIT_CHAR)
        for p in paths:
            item = item[p]
    except KeyError:
        return False
    return True


def remove_duplicates(dic, only_keys=True):
    """
    Use a reverse dict to ensure there are no duplicate values
    If only_keys is false, it will return the dict of unique values
    """
    result = {}
    for key, value in merge_list_of_dicts(dic).items():
        if value not in result.values():
            result[key] = value
    if only_keys:
        return list(result.keys())
    return result


def reverse_dict(dic):
    return {v: k for k, v in dic.items()}


def listify(dic):
    return [{k: v} for k, v in dic.items()]
