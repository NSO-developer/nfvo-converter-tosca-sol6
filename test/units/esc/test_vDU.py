import unittest
from src.util import Util


class TestvDU(unittest.TestCase):

    def setUp(self):
        self.vDU = Util.solcon("altiostar_vDU.yaml")

    def test_one(self):
        self.assertEqual(1, 1)
