import unittest
from src.util import Util


class TestvCU(unittest.TestCase):

    # Use this method to load the vnfd, since otherwise it loads one every time
    @classmethod
    def setUpClass(cls):
        cls.vnfd = Util.solcon("altiostar_vCU.yaml")

    # *****************
    # *** VNF Tests ***
    # *****************
    def test_sanity(self):
        print(self)
        self.assertGreater(len(self.vnfd), 0)

    # More than 1 thing exists
    def test_exist_contents(self):
        self.assertGreaterEqual(len(self.vnfd["vnfd"]), 1)

    # *************************
    # *** Vitual Link Tests ***
    # *************************
    def test_int_virt_cpd_exists(self):
        self.assertIn("int-virtual-link-desc", self.vnfd["vnfd"])

    def test_int_virt_cpd_length(self):
        self.assertGreaterEqual(len(self.vnfd["vnfd"]["int-virtual-link-desc"]), 3)

    # *********************
    # *** EXT CPD Tests ***
    # *********************
    def test_ext_cpd_exists(self):
        self.assertIn("ext-cpd", self.vnfd["vnfd"])

    def test_ext_cpd_length(self):
        self.assertGreaterEqual(len(self.vnfd["vnfd"]["ext-cpd"]), 1)

    # *****************
    # *** VDU Tests ***
    # *****************
    def test_vdu_exists(self):
        self.assertIn("vdu", self.vnfd["vnfd"])

    def test_vdu_length(self):
        self.assertEqual(len(self.vnfd["vnfd"]["vdu"]), 1)

    def test_vdu_storage_desc(self):
        for i in range(len(self.vnfd["vnfd"]["vdu"])):
            with self.subTest(i=i):
                self.assertIn("virtual-storage-desc", self.vnfd["vnfd"]["vdu"][i])

