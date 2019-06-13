import itertools


def flatten(to_flatten):
    """
    Takes any number of lists inside a list and turns it into a single flat list
    [1, 2, [3, 4, 5], [66, 33, 22]]
    => [1, 2, 3, 4, 5, 66, 33, 22]
    :param to_flatten: nested lists
    :returns: list
    """
    return list(itertools.chain.from_iterable(to_flatten))
