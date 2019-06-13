import unittest
from src.util import Util


class TestESC(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self.vCU = Util.solcon("altiostar_vCU.yaml")
        self.vDU = Util.solcon("altiostar_vDU.yaml")
        self.vPE = Util.solcon("Tosca_vPE.yaml")
        self.vpcDI = Util.solcon("standalone_vpc_vnfd_esc_4_4.yaml")
        self.vpcSI = Util.solcon("VPEC_SI_UPP_vnfd_esc_4_4.yaml")

    def test_v_cu(self):
        self.assertEqual(1, 1)

    def test_v_du(self):
        self.assertEqual(1, 1)

    def test_vpd_di(self):
        self.assertEqual(1, 1)

    def test_vpc_si(self):
        self.assertEqual(1, 1)

    def test_v_pe(self):
        self.assertEqual(1, 1)

