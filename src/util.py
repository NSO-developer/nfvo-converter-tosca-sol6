from solcon import *
"""
Test util file, it should be moved into test/ in the future
"""


class Util:
    @staticmethod
    def solcon(file, config="config-esc.toml"):
        # Disable
        sys.stdout = open(os.devnull, 'w')
        s = SolCon(internal_run=True, internal_args=Util.format_args(file, con=config))
        sys.stdout = sys.__stdout__
        return s.cnfv

    @staticmethod
    def format_args(f, con, r=None):
        c = "../../config/{}".format(con)
        s = "../../config/config-sol6.toml"
        l_l = "CRITICAL"
        a = {"f": "../../examples/esc/{}".format(f), "o": None, "c": c, "s": s, "r": r, "l": l_l}
        return a
