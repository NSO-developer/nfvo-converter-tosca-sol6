from solcon import *
"""
Test util file, it should be moved into test/ in the future
"""


class Util:
    root = "../../"
    @staticmethod
    def solcon(file, config="config-esc.toml"):
        # Remove '../' to root if you're running it via unit_tests.py
        s = SolCon(internal_run=True, internal_args=Util.format_args(file, con=config, root=Util.root))
        return s.cnfv

    @staticmethod
    def format_args(f, con, r=None, root=""):
        c = "{}config/{}".format(root, con)
        # s = "{}config/example-sol6-config.toml".format(root)
        l_l = 50  # critical
        o_silent = True
        a = {"f": "{}examples/esc/{}".format(root, f), "o": None, "c": c, "r": r, "l": l_l, "e": o_silent}
        return a
