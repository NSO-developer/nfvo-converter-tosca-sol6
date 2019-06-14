import unittest
from src.util import Util


class TestvCU(unittest.TestCase):

    def setUp(self):
        self.vCU = Util.solcon("altiostar_vCU.yaml")

    def test_one(self):
        self.assertEqual(1, 1)
