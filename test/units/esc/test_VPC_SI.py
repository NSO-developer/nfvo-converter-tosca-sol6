import unittest
from src.util import Util


class TestVPCSI(unittest.TestCase):

    def setUp(self):
        self.vnfd = None
       #self.vnfd = Util.solcon("VPEC_SI_UPP_vnfd_esc_4_4.yaml")

    def test_one(self):
        self.assertEqual(1, 1)
