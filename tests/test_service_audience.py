# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
import unittest
from xml.etree import ElementTree

from odxtools.service import DiagService
from odxtools.odxlink import OdxDocFragment

doc_frags = [OdxDocFragment("UnitTest", "WinnieThePoh")]


class TestDiagServiceAudience(unittest.TestCase):
    def test_audience_with_no_child_elements_is_still_parsed(self):
        """A self-closing AUDIENCE tag with only attributes must not be treated as absent"""
        et_element = ElementTree.fromstring("""
            <DIAG-SERVICE ID="service.test">
                <SHORT-NAME>test_service</SHORT-NAME>
                <REQUEST-REF ID-REF="request.test"/>
                <AUDIENCE IS-SUPPLIER="false"/>
            </DIAG-SERVICE>
        """)

        service = DiagService.from_et(et_element, doc_frags)

        self.assertIsNotNone(service.audience)
        self.assertFalse(service.audience.is_supplier)


if __name__ == "__main__":
    unittest.main()