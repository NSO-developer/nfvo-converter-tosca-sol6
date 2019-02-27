class KeyUtils:
    """
    General utility methods to use on paths from this file

    """
    @staticmethod
    def get_path_last(path, n=1):
        """
        Get the n last elements of the path, with their separators between them
        """
        paths = path.split(".")
        if len(paths) > 0:
            return ".".join(paths[len(paths) - n:len(paths)])
        raise KeyError("Path {} is an invalid path to use in this method.".format(path))

    @staticmethod
    def remove_path_first(path, n=1):
        """ Get the string without the first n elements of the path """
        paths = path.split(".")
        if len(paths) > 0:
            return ".".join(paths[n:len(paths)])
        raise KeyError("Path {} is an invalid path to use in this method.".format(path))

    @staticmethod
    def remove_path_level(path, path_level):
        return KeyUtils.remove_path_first(path, KeyUtils.get_path_level(path_level))

    @staticmethod
    def remove_path_elem(path, elem):
        """
        Remove the given elem of the path, return the path string without that element
        """
        paths = path.split(".")
        del paths[elem]
        return ".".join(paths)

    @staticmethod
    def get_path_level(path):
        return path.count(".") + 1
