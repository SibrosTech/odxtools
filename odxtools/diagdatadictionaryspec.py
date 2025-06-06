# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING, Optional, Any, Dict, List

from .utils import short_name_as_id
from .dataobjectproperty import (
    DataObjectProperty,
    DtcDop,
)
from .endofpdufield import EndOfPduField
from .envdata import EnvironmentData
from .envdatadesc import EnvironmentDataDescription
from .globals import logger
from .multiplexer import Multiplexer
from .nameditemlist import NamedItemList
from .structures import BasicStructure, create_any_structure_from_et
from .table import Table
from .units import UnitSpec
from .odxlink import OdxLinkId, OdxLinkDatabase, OdxDocFragment
from .specialdata import SpecialDataGroup, create_sdgs_from_et

if TYPE_CHECKING:
    from .diaglayer import DiagLayer

@dataclass
class DiagDataDictionarySpec:
    dtc_dops: NamedItemList[DtcDop]
    data_object_props: NamedItemList[DataObjectProperty]
    structures: NamedItemList[BasicStructure]
    end_of_pdu_fields: NamedItemList[EndOfPduField]
    tables: NamedItemList[Table]
    env_data_descs: NamedItemList[EnvironmentDataDescription]
    env_datas: NamedItemList[EnvironmentData]
    muxs: NamedItemList[Multiplexer]
    unit_spec: Optional[UnitSpec]
    sdgs: List[SpecialDataGroup]

    def __post_init__(self):
        self._all_data_object_properties = \
            NamedItemList(short_name_as_id,
                          chain(self.data_object_props,
                                self.structures,
                                self.end_of_pdu_fields,
                                self.dtc_dops,
                                self.tables))

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) \
            -> "DiagDataDictionarySpec":
        # Parse DOP-BASEs
        data_object_props = [
            DataObjectProperty.from_et(dop_element, doc_frags)
            for dop_element in et_element.iterfind("DATA-OBJECT-PROPS/DATA-OBJECT-PROP")
        ]

        structures = []
        for structure_element in et_element.iterfind("STRUCTURES/STRUCTURE"):
            structure = create_any_structure_from_et(structure_element, doc_frags)
            assert structure is not None
            structures.append(structure)

        end_of_pdu_fields = [
            EndOfPduField.from_et(eofp_element, doc_frags)
            for eofp_element in et_element.iterfind("END-OF-PDU-FIELDS/END-OF-PDU-FIELD")
        ]

        dtc_dops = []
        for dop_element in et_element.iterfind("DTC-DOPS/DTC-DOP"):
            dop = DtcDop.from_et(dop_element, doc_frags)
            assert isinstance(dop, DtcDop)
            dtc_dops.append(dop)

        tables = [
            Table.from_et(table_element, doc_frags)
            for table_element in et_element.iterfind("TABLES/TABLE")
        ]

        env_data_descs = [
            EnvironmentDataDescription.from_et(env_data_desc_element, doc_frags)
            for env_data_desc_element in et_element.iterfind("ENV-DATA-DESCS/ENV-DATA-DESC")
        ]

        env_data_elements = chain(
            et_element.iterfind("ENV-DATAS/ENV-DATA"),
            # ODX 2.0.0 says ENV-DATA-DESC could contain a list of ENV-DATAS
            et_element.iterfind("ENV-DATA-DESCS/ENV-DATA-DESC/ENV-DATAS/ENV-DATA"),
        )
        env_datas = [
            EnvironmentData.from_et(env_data_element, doc_frags)
            for env_data_element in env_data_elements
        ]

        muxs = [
            Multiplexer.from_et(mux_element, doc_frags)
            for mux_element in et_element.iterfind("MUXS/MUX")
        ]

        if et_element.find("UNIT-SPEC") is not None:
            unit_spec = UnitSpec.from_et(et_element.find("UNIT-SPEC"), doc_frags)
        else:
            unit_spec = None

        # TODO: Parse different specs.. Which of them are needed?
        for (path, name) in [
            ("STATIC-FIELDS", "static fields"),
            ("DYNAMIC-LENGTH-FIELDS/DYNAMIC-LENGTH-FIELD", "dynamic length fields"),
            (
                "DYNAMIC-ENDMARKER-FIELDS/DYNAMIC-ENDMARKER-FIELD",
                "dynamic endmarker fields",
            ),
        ]:
            num = len(list(et_element.iterfind(path)))
            if num > 0:
                logger.info(f"Not implemented: Did not parse {num} {name}.")

        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return DiagDataDictionarySpec(
            data_object_props=NamedItemList(short_name_as_id, data_object_props),
            structures=NamedItemList(short_name_as_id, structures),
            end_of_pdu_fields=NamedItemList(short_name_as_id, end_of_pdu_fields),
            dtc_dops=NamedItemList(short_name_as_id, dtc_dops),
            unit_spec=unit_spec,
            tables=NamedItemList(short_name_as_id, tables),
            env_data_descs=NamedItemList(short_name_as_id, env_data_descs),
            env_datas=NamedItemList(short_name_as_id, env_datas),
            muxs=NamedItemList(short_name_as_id, muxs),
            sdgs=sdgs,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = {}
        for obj in chain(self.data_object_props,
                         self.structures,
                         self.end_of_pdu_fields,
                         self.tables,
                         ):
            odxlinks[obj.odx_id] = obj

        for obj in chain(self.data_object_props,
                         self.dtc_dops,
                         self.env_data_descs,
                         self.env_datas,
                         self.muxs,
                         self.sdgs,
                         self.structures,
                         self.end_of_pdu_fields,
                         self.tables,
                         ):
            odxlinks.update(obj._build_odxlinks())

        if self.unit_spec is not None:
            odxlinks.update(self.unit_spec._build_odxlinks())

        return odxlinks

    def _resolve_references(self,
                            parent_dl: "DiagLayer",
                            odxlinks: OdxLinkDatabase):

        for obj in self.data_object_props:
            obj._resolve_references(odxlinks)
        for obj in self.dtc_dops:
            obj._resolve_references(odxlinks)
        for obj in self.end_of_pdu_fields:
            obj._resolve_references(parent_dl, odxlinks)
        for obj in self.env_data_descs:
            obj._resolve_references(odxlinks)
        for obj in self.env_datas:
            obj._resolve_references(parent_dl, odxlinks)
        for obj in self.muxs:
            obj._resolve_references(odxlinks)
        for obj in self.sdgs:
            obj._resolve_references(odxlinks)
        for obj in self.structures:
            obj._resolve_references(parent_dl, odxlinks)
        for obj in self.tables:
            obj._resolve_references(odxlinks)

        if self.unit_spec:
            self.unit_spec._resolve_references(odxlinks)

    @property
    def all_data_object_properties(self):
        return self._all_data_object_properties
