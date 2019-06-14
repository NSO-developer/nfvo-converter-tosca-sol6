from solcon import *
"""
Test util file, it should be moved into test/ in the future
"""


class Util:
    @staticmethod
    def solcon(file, config="config-esc.toml", root="../"):
        # Disable
        s = SolCon(internal_run=True, internal_args=Util.format_args(file, con=config, root=root))
        return s.cnfv

    @staticmethod
    def format_args(f, con, r=None, root=""):
        c = "{}config/{}".format(root, con)
        s = "{}config/config-sol6.toml".format(root)
        l_l = 50  # critical
        o_silent = True
        a = {"f": "{}examples/esc/{}".format(root, f), "o": None, "c": c, "s": s, "r": r, "l": l_l, "e": o_silent}
        return a
