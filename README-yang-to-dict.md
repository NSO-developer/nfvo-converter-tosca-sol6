# YANG To Dict Tool
This class is designed to be a semi-generic way of taking a specification YANG file and turning it
into an empty dictionary to be used making it easier to assign values to the proper places with
the correct names.

For example, given the following specification yang file:

    grouping test_grouping {
        list first_list {
            leaf name {
                type string;
            }
            leaf desc {
                type string;
            }
        }
        leaf group_name {
            type string;
        }
    }

The program would produce a dict that looked like this:

    {'test_grouping' : { 'first_list': {'name': '', 'desc': '' }, 'group_name': '' } }



This type of structure is designed to be copied and used as a template for assigning values to.


## ALGORITHM

1. pre) A list called cur_elem is always kept up to date with the stack of our current location
    This list corresponds with the keys inside dict_result and is used to traverse the dictionary.

2. Read the file
3. Search the file for the first grouping tag (configurable)
4. Push that grouping onto the 'dictstack'

5. Start looping through the file, if we find a "grouping, list, leaf, or '}'" then call the
    relevant method to parse it.
    1. (list) Find the current element in the final dict, then initialize a new sub-dict at at the name
    of this list in the final dict. Note: grouping is handled here.
    
    2. (leaf) Loop through the cur_elem list, traversing the dict up until we run out of elements,
    at that point create a new entry in the current dict context and assign it a blank string.

    3. (}) In order to keep proper context and stack order, pop the top of the cur_elem list

6. Return dict_result
