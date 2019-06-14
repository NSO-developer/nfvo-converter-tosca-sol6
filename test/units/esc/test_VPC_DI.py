import unittest
from src.util import Util


class TestVPCDI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vnfd = Util.solcon("standalone_vpc_vnfd_esc_4_4.yaml")

    def test_one(self):
        self.assertEqual(1, 1)
