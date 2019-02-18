#!/usr/bin/env python3
"""
Input a yang file and this script will output an empty dict with the fields of the yang populated.
"""

GROUPING = 'grouping '
LEAF = 'leaf '
LIST = 'list '
B_START = '{'
B_END = '}'


class YangToDict:

    file = None
    log = None
    grouping_required = True
    lines = []
    lines_used = []
    cur_line = -1
    dict_result = {}
    # For every open bracket we append *something* to this, and every closing bracket pops one off
    cur_elem = []

    def __init__(self, file=None, log=None, g_req=True):
        self.log = log
        self.grouping_required = g_req
        self.file = file

    def parse_yang(self):
        """
        Take a yang specification file as input, output it and it's values as a dict
        The yang file is supposed to be used like a template, so there are no actual values for the
        leaves.
        """

        self.lines = self._read_file()
        self.lines_used = [False]*len(self.lines)

        # Find the first 'grouping' tag and start there
        self.cur_line = self._find_start()

        self._main_loop()

        used = sum(self.lines_used)
        # print("Used {} lines out of {} = {}%".format(used, len(self.lines),
        #                                             round((used/len(self.lines))*100, 2)))
        print("{}% of SOL6 YANG used".format(round((used/len(self.lines))*100, 2)))

        return self.dict_result

    def _main_loop(self):
        while True:
            # Just keep looping until we've processed the whole file
            if self.cur_line >= len(self.lines):
                return

            # Determine what we're dealing with right now
            c_l = self.lines[self.cur_line]
            if c_l.startswith('//'):
                self._use_line()
                pass
            elif GROUPING in c_l:
                self._parse_grouping()
            elif LEAF in c_l:
                self._parse_leaf()
            elif LIST in c_l:
                self._parse_list()
            elif B_END in c_l:
                self._parse_end_bracket()
            elif B_START in c_l:
                # If we hit something we don't support, we need to keep the stack in the right order
                self._use_line()
                self.cur_elem.append(B_START)

            self.cur_line += 1

    def _parse_grouping(self):
        """
        Assuming that grouping is at top-level.
        In the future, change this to work pretty much exactly like list
        """

        is_code, group_name = ensure_bracket(self.lines[self.cur_line].split(" "))

        if not is_code:
            return

        # Initialize a new dict at this location in the dict_result
        context = context_top_elems(self.cur_elem, self.dict_result)

        # Initialize the new dict
        context[group_name] = {}

        self.dict_result[group_name] = {}
        self.cur_elem.append(group_name)
        self._use_line()

    def _parse_list(self):
        """
        Groupings are considered lists.
        Create a new sub-dict at our current element in the dict_result.
        """
        is_code, list_name = ensure_bracket(self.lines[self.cur_line].split(" "))

        if not is_code:
            return
        # Initialize a new dict at this location in the dict_result
        context = context_top_elems(self.cur_elem, self.dict_result)

        # Initialize the new list
        context[list_name] = []

        # Assumption: We are always going to be storing dicts in these lists
        context[list_name].append({})

        self.cur_elem.append(list_name)
        self._use_line()

    def _parse_leaf(self):
        """
        Get the name of the leaf and assign it a blank string value so we can populate it later
        """
        is_code, leaf_name = ensure_bracket(self.lines[self.cur_line].split(" "))

        if not is_code:
            return

        # If we are anywhere but in the root of the dict, get our current element
        if len(self.cur_elem) > 1:
            dic = context_top_elems(self.cur_elem, self.dict_result)
        else:  # At the root, just initialize the name of the current element
            dic = self.dict_result[self.cur_elem[0]]

        if type(dic) is list:
            dic = dic[0]

        dic[leaf_name] = ""
        self.cur_elem.append(B_START)
        self._use_line()

    def _parse_end_bracket(self):
        """
        Remove at least one element from cur_elem list
        """
        if len(self.cur_elem) > 1:
            self.cur_elem.pop()
        else:
            self.cur_elem = []

        self._use_line()

    # ************* Utility Methods ******************
    def _read_file(self):
        """
        Take a filename as input, read it into a list of separate lines, and strip all
        leading/trailing whitespace from the lines
        """
        return list(map(str.strip, open(self.file).read().splitlines()))

    def _find_start(self):
        """
        Right now we don't care about the start of the file, we only care about the grouping tags
        :return: index where grouping starts
        """

        for i in range(len(self.lines)):
            if GROUPING in self.lines[i]:
                return i
        # If we can't find it then this probably isn't something we support
        if not self.grouping_required:
            self.log.info("Grouping tag not required and not found ")
        else:
            raise EOFError("'grouping' not found")

    def _use_line(self):  # Mark the current line as used
        self.lines_used[self.cur_line] = True


# *** Static Methods ***
def context_top_elems(cur_elem, dict_result):
    """
    Given a list of elements, return the object that is in the dict at that point
    dict_result = {'root': {'list1': ['dict1': {key: ""}  ] }
    cur_elem = ['root', 'list1', 'dict1']
    Should return a reference to a dict that is dict_result['dict1']
    """
    top = dict_result
    for i in cur_elem:
        # This is also called from leaves
        # So if we reach a point where a leaf requires something to write to, don't return
        # the non-existant dict ['{']
        if i == B_START:
            break
        # We need to handle if we are getting into a list, since getting a dict in a list is
        # part of the functionality
        if type(top) is list:
            if len(top) > 0:
                top = top[0]

        top = top[i]

    if type(top) is list:
        return top[0]
    return top


def ensure_bracket(lst):
    """
    Make sure the last element of the list is a bracket, then return the second-from-the-last elem
    """
    if lst[-1] == B_START:
        return True, lst[-2]
    else:
        return False, lst


def count_empty_fields(cur_elem):
    """
    Loop through the whole dict and count the number of fields that contain empty values,
    such as empty lists or empty dicts
    """
    empty_elems = 0
    if type(cur_elem) is dict:
        if len(cur_elem.items()) == 0:
            empty_elems += 1

        for k, v in cur_elem.items():
            c_e = v
            if type(v) is not str:
                c_e = cur_elem[k]
            if not c_e:
                empty_elems += 1
            else:
                empty_elems += count_empty_fields(c_e)

    elif type(cur_elem) is list:
        if not cur_elem:
            empty_elems += 1
        for i in cur_elem:
            if not i:
                empty_elems += 1
            else:
                empty_elems += count_empty_fields(i)
    elif type(cur_elem) is str:
        if not cur_elem:
            empty_elems += 1
    return empty_elems
