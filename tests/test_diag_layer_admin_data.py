# SPDX-License-Identifier: MIT
import unittest
from xml.etree import ElementTree

from odxtools.diaglayer import DiagLayer
from odxtools.odxlink import OdxDocFragment

# the document fragment which is used throughout the test
doc_frags = [OdxDocFragment("UnitTest", "unit_test_doc")]

BASE_VARIANT_XML = """
<BASE-VARIANT ID="BV.ebcm">
  <SHORT-NAME>EBCM</SHORT-NAME>
  <ADMIN-DATA>
    <DOC-REVISIONS>
      <DOC-REVISION>
        <REVISION-LABEL>6.1.4</REVISION-LABEL>
        <DATE>2026-08-01T09:00:00+05:30</DATE>
      </DOC-REVISION>
      <DOC-REVISION>
        <REVISION-LABEL>6.1.5</REVISION-LABEL>
        <DATE>2026-09-10T09:56:07+05:30</DATE>
      </DOC-REVISION>
    </DOC-REVISIONS>
  </ADMIN-DATA>
</BASE-VARIANT>
"""

BASE_VARIANT_WITHOUT_ADMIN_DATA_XML = """
<BASE-VARIANT ID="BV.ebcm">
  <SHORT-NAME>EBCM</SHORT-NAME>
</BASE-VARIANT>
"""


class TestDiagLayerAdminData(unittest.TestCase):

    def test_admin_data_of_base_variant_is_parsed(self):
        dl = DiagLayer.from_et(ElementTree.fromstring(BASE_VARIANT_XML), doc_frags)

        self.assertIsNotNone(dl.admin_data)
        self.assertEqual([dr.revision_label for dr in dl.admin_data.doc_revisions],
                         ["6.1.4", "6.1.5"])

    def test_admin_data_is_none_when_absent(self):
        dl = DiagLayer.from_et(ElementTree.fromstring(BASE_VARIANT_WITHOUT_ADMIN_DATA_XML),
                               doc_frags)

        self.assertIsNone(dl.admin_data)


if __name__ == "__main__":
    unittest.main()
