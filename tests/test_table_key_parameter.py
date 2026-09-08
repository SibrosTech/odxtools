# SPDX-License-Identifier: MIT
import unittest
from xml.etree import ElementTree

from odxtools.odxlink import OdxDocFragment, OdxLinkDatabase
from odxtools.parameters.createanyparameter import create_any_parameter_from_et
from odxtools.table import Table

# the document fragment which is used throughout the test
doc_frags = [OdxDocFragment("UnitTest", "unit_test_doc")]

TABLE_XML = """
<TABLE ID="table.flip_quality">
  <SHORT-NAME>flip_quality</SHORT-NAME>
  <TABLE-ROW ID="table.flip_quality.best">
    <SHORT-NAME>best</SHORT-NAME>
    <KEY>10</KEY>
  </TABLE-ROW>
</TABLE>
"""

# a TABLE-KEY which pins one row via TABLE-ROW-REF and hence names
# neither TABLE-REF nor TABLE-SNREF
TABLE_KEY_XML = """
<PARAM xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       ID="param.flip_quality_key" xsi:type="TABLE-KEY">
  <SHORT-NAME>flip_quality_key</SHORT-NAME>
  <TABLE-ROW-REF ID-REF="table.flip_quality.best"/>
</PARAM>
"""


class TestTableKeyParameter(unittest.TestCase):

    def test_table_resolved_from_table_row_ref(self):
        table = Table.from_et(ElementTree.fromstring(TABLE_XML), doc_frags)
        param = create_any_parameter_from_et(ElementTree.fromstring(TABLE_KEY_XML), doc_frags)

        odxlinks = OdxLinkDatabase()
        # DiagDataDictionarySpec registers the table itself, Table only its rows
        odxlinks.update({table.odx_id: table})
        odxlinks.update(table._build_odxlinks())
        odxlinks.update(param._build_odxlinks())

        table._resolve_references(odxlinks)
        param._resolve_references(None, odxlinks)

        self.assertEqual(param.table, table)
        self.assertEqual(param.table_row.short_name, "best")


if __name__ == "__main__":
    unittest.main()
