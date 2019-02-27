from sol6_keys import *


class TOSCA(TOSCA):
    pass


class SOL6(SOL6):
    pass


class V2Map(V2Map):
    def __init__(self, dict_tosca, dict_sol6, log=None):
        super().__init__(dict_tosca, dict_sol6, log)


