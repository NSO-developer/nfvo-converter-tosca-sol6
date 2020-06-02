import unittest
from utils.util import Util


class TestvPE(unittest.TestCase):

    # Use this method to load the vnfd, since otherwise it loads one every time
    @classmethod
    def setUpClass(cls):
        cls.vnfd = Util.solcon("Tosca_vPE.yaml")
        cls.vdus = cls.vnfd["vnfd"]["vdu"]

    # *****************
    # *** VNF Tests ***
    # *****************
    def test_sanity(self):
        self.assertGreater(len(self.vnfd), 0)

    # More than 1 thing exists
    def test_exist_contents(self):
        self.assertGreaterEqual(len(self.vnfd["vnfd"]), 1)

    # *************************
    # *** Virtual Link Tests ***
    # *************************
    def test_int_virt_cpd_length(self):
        self.assertIn("int-virtual-link-desc", self.vnfd["vnfd"])
        self.assertGreaterEqual(len(self.vnfd["vnfd"]["int-virtual-link-desc"]), 3)

    def test_int_virt_cpd_duplicates(self):
        virt_link_ids = [elem["id"] for elem in self.vnfd["vnfd"]["int-virtual-link-desc"]]
        self.assertEqual(len(set(virt_link_ids)), len(virt_link_ids))

    # *********************
    # *** EXT CPD Tests ***
    # *********************
    def test_ext_cpd_length(self):
        self.assertIn("ext-cpd", self.vnfd["vnfd"])
        self.assertGreaterEqual(len(self.vnfd["vnfd"]["ext-cpd"]), 1)

    # *****************
    # *** VDU Tests ***
    # *****************
    def test_vdu_exists(self):
        self.assertIn("vdu", self.vnfd["vnfd"])

    def test_vdu_length(self):
        self.assertEqual(len(self.vdus), 1)

    def test_vdu_compute_desc(self):
        self._assertIn_subtests(len(self.vdus), "virtual-compute-desc", self.vdus)

    def test_vdu_sw_img_desc(self):
        self._assertIn_subtests(len(self.vdus), "sw-image-desc", self.vdus)

    def test_vdu_count_int_cpds(self):
        with self.subTest(i=0):
            self.assertEqual(len(self.vdus[0]["int-cpd"]), 5)

    # *******************************
    # *** Deployment Flavor Tests ***
    # *******************************
    def test_df_exist(self):
        self.assertIn("df", self.vnfd["vnfd"])
        df = self.vnfd["vnfd"]["df"]
        self.assertIn("instantiation-level", df)
        self.assertIn("vdu-profile", df)

    # **********************
    # *** Artifact Tests ***
    # **********************
    def test_artifacts(self):
        self.assertFalse("cisco-etsi-nfvo:artifact" not in self.vnfd["vnfd"])

        for i, a in enumerate(self.vnfd["vnfd"]["cisco-etsi-nfvo:artifact"]):
            with self.subTest(i=i):
                self.assertIn("id", a)
                self.assertIn("url", a)
                self.assertIn("checksum", a)

    # *** Helper Methods ***
    def _assertIn_subtests(self, leng, name, loc):
        for i in range(leng):
            with self.subTest(i=i):
                self.assertIn(name, loc[i])
