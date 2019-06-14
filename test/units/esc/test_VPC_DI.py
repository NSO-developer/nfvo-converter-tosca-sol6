import unittest
from src.util import Util


class TestVPCDI(unittest.TestCase):

    def setUp(self):
        self.vpc_di = Util.solcon("standalone_vpc_vnfd_esc_4_4.yaml")

    def test_one(self):
        self.assertEqual(1, 1)
