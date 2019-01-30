import inspect


class ConverterErrors:
    ERR_001 = "001: Specified path/key {} not found in {}"

    _log = None

    def __init__(self, log=None):
        self._log = log


def log(variables, code):
    print("ERROR: ", code.format(variables), inspect.stack()[1][3])
