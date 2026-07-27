"""
Auto generated file. DO NOT EDIT.
Source: tidas_flows_elementary_category.json
"""
from __future__ import annotations

from typing import Literal, Union

from pydantic import Field
from tidas_sdk.core.base import TidasBaseModel

class FlowsElementaryCategoryVariant0(TidasBaseModel):
    level: Literal['0'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant1(TidasBaseModel):
    level: Literal['1'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.1'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to water'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant2(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.1.1'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to fresh water'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant3(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.1.2'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to sea water'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant4(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.1.3'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to water, unspecified'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant5(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.1.4'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to water, unspecified (long-term)'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant6(TidasBaseModel):
    level: Literal['1'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.2'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to soil'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant7(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.2.1'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to agricultural soil'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant8(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.2.2'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to non-agricultural soil'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant9(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.2.3'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to soil, unspecified'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant10(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.2.4'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to soil, unspecified (long-term)'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant11(TidasBaseModel):
    level: Literal['1'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.3'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to air'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant12(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.3.1'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to urban air close to ground'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant13(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.3.2'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to non-urban air or from high stacks'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant14(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.3.3'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to lower stratosphere and upper troposphere'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant15(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.3.4'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to air, unspecified'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant16(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.3.5'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to air, unspecified (long-term)'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant17(TidasBaseModel):
    level: Literal['0'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2'] | None = Field(default=None, alias='@catId')
    text: Literal['Resources'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant18(TidasBaseModel):
    level: Literal['1'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.1'] | None = Field(default=None, alias='@catId')
    text: Literal['Resources from ground'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant19(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.1.1'] | None = Field(default=None, alias='@catId')
    text: Literal['Non-renewable material resources from ground'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant20(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.1.2'] | None = Field(default=None, alias='@catId')
    text: Literal['Non-renewable element resources from ground'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant21(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.1.3'] | None = Field(default=None, alias='@catId')
    text: Literal['Non-renewable energy resources from ground'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant22(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.1.4'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable element resources from ground'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant23(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.1.5'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable energy resources from ground'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant24(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.1.6'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable material resources from ground'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant25(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.1.7'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable resources from ground, unspecified'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant26(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.1.8'] | None = Field(default=None, alias='@catId')
    text: Literal['Non-renewable resources from ground, unspecified'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant27(TidasBaseModel):
    level: Literal['1'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.2'] | None = Field(default=None, alias='@catId')
    text: Literal['Resources from water'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant28(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.2.1'] | None = Field(default=None, alias='@catId')
    text: Literal['Non-renewable material resources from water'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant29(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.2.2'] | None = Field(default=None, alias='@catId')
    text: Literal['Non-renewable element resources from water'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant30(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.2.3'] | None = Field(default=None, alias='@catId')
    text: Literal['Non-renewable energy resources from water'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant31(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.2.4'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable element resources from water'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant32(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.2.5'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable energy resources from water'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant33(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.2.6'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable material resources from water'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant34(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.2.7'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable resources from water, unspecified'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant35(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.2.8'] | None = Field(default=None, alias='@catId')
    text: Literal['Non-renewable resources from water, unspecified'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant36(TidasBaseModel):
    level: Literal['1'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.3'] | None = Field(default=None, alias='@catId')
    text: Literal['Resources from air'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant37(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.3.1'] | None = Field(default=None, alias='@catId')
    text: Literal['Non-renewable material resources from air'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant38(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.3.2'] | None = Field(default=None, alias='@catId')
    text: Literal['Non-renewable element resources from air'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant39(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.3.3'] | None = Field(default=None, alias='@catId')
    text: Literal['Non-renewable energy resources from air'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant40(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.3.4'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable element resources from air'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant41(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.3.5'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable energy resources from air'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant42(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.3.6'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable material resources from air'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant43(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.3.7'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable resources from air, unspecified'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant44(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.3.8'] | None = Field(default=None, alias='@catId')
    text: Literal['Non-renewable resources from air, unspecified'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant45(TidasBaseModel):
    level: Literal['1'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.4'] | None = Field(default=None, alias='@catId')
    text: Literal['Resources from biosphere'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant46(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.4.1'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable element resources from biosphere'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant47(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.4.2'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable energy resources from biosphere'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant48(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.4.3'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable material resources from biosphere'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant49(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.4.4'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable genetic resources from biosphere'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant50(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['2.4.5'] | None = Field(default=None, alias='@catId')
    text: Literal['Renewable resources from biosphere, unspecified'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant51(TidasBaseModel):
    level: Literal['0'] | None = Field(default=None, alias='@level')
    cat_id: Literal['3'] | None = Field(default=None, alias='@catId')
    text: Literal['Land use'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant52(TidasBaseModel):
    level: Literal['1'] | None = Field(default=None, alias='@level')
    cat_id: Literal['3.1'] | None = Field(default=None, alias='@catId')
    text: Literal['Land occupation'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant53(TidasBaseModel):
    level: Literal['1'] | None = Field(default=None, alias='@level')
    cat_id: Literal['3.2'] | None = Field(default=None, alias='@catId')
    text: Literal['Land transformation'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant54(TidasBaseModel):
    level: Literal['0'] | None = Field(default=None, alias='@level')
    cat_id: Literal['4'] | None = Field(default=None, alias='@catId')
    text: Literal['Other elementary flows'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant55(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.3.6'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to air, indoor'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant56(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.3.7'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to urban air low stack'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant57(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.3.8'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to urban air high stack'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant58(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.3.9'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to urban air very high stack'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant59(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.3.10'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to non-urban air close to ground'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant60(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.3.11'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to non-urban air low stack'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant61(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.3.12'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to non-urban air high stack'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant62(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.3.13'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to non-urban air very high stack'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant63(TidasBaseModel):
    level: Literal['1'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.4'] | None = Field(default=None, alias='@catId')
    text: Literal['Emissions to industrial soil'] | None = Field(default=None, alias='#text')

class FlowsElementaryCategoryVariant64(TidasBaseModel):
    level: Literal['2'] | None = Field(default=None, alias='@level')
    cat_id: Literal['1.4.1'] | None = Field(default=None, alias='@catId')
    text: Literal['Other emissions to industrial soil'] | None = Field(default=None, alias='#text')

FlowsElementaryCategory = Union[
    FlowsElementaryCategoryVariant0,
    FlowsElementaryCategoryVariant1,
    FlowsElementaryCategoryVariant2,
    FlowsElementaryCategoryVariant3,
    FlowsElementaryCategoryVariant4,
    FlowsElementaryCategoryVariant5,
    FlowsElementaryCategoryVariant6,
    FlowsElementaryCategoryVariant7,
    FlowsElementaryCategoryVariant8,
    FlowsElementaryCategoryVariant9,
    FlowsElementaryCategoryVariant10,
    FlowsElementaryCategoryVariant11,
    FlowsElementaryCategoryVariant12,
    FlowsElementaryCategoryVariant13,
    FlowsElementaryCategoryVariant14,
    FlowsElementaryCategoryVariant15,
    FlowsElementaryCategoryVariant16,
    FlowsElementaryCategoryVariant17,
    FlowsElementaryCategoryVariant18,
    FlowsElementaryCategoryVariant19,
    FlowsElementaryCategoryVariant20,
    FlowsElementaryCategoryVariant21,
    FlowsElementaryCategoryVariant22,
    FlowsElementaryCategoryVariant23,
    FlowsElementaryCategoryVariant24,
    FlowsElementaryCategoryVariant25,
    FlowsElementaryCategoryVariant26,
    FlowsElementaryCategoryVariant27,
    FlowsElementaryCategoryVariant28,
    FlowsElementaryCategoryVariant29,
    FlowsElementaryCategoryVariant30,
    FlowsElementaryCategoryVariant31,
    FlowsElementaryCategoryVariant32,
    FlowsElementaryCategoryVariant33,
    FlowsElementaryCategoryVariant34,
    FlowsElementaryCategoryVariant35,
    FlowsElementaryCategoryVariant36,
    FlowsElementaryCategoryVariant37,
    FlowsElementaryCategoryVariant38,
    FlowsElementaryCategoryVariant39,
    FlowsElementaryCategoryVariant40,
    FlowsElementaryCategoryVariant41,
    FlowsElementaryCategoryVariant42,
    FlowsElementaryCategoryVariant43,
    FlowsElementaryCategoryVariant44,
    FlowsElementaryCategoryVariant45,
    FlowsElementaryCategoryVariant46,
    FlowsElementaryCategoryVariant47,
    FlowsElementaryCategoryVariant48,
    FlowsElementaryCategoryVariant49,
    FlowsElementaryCategoryVariant50,
    FlowsElementaryCategoryVariant51,
    FlowsElementaryCategoryVariant52,
    FlowsElementaryCategoryVariant53,
    FlowsElementaryCategoryVariant54,
    FlowsElementaryCategoryVariant55,
    FlowsElementaryCategoryVariant56,
    FlowsElementaryCategoryVariant57,
    FlowsElementaryCategoryVariant58,
    FlowsElementaryCategoryVariant59,
    FlowsElementaryCategoryVariant60,
    FlowsElementaryCategoryVariant61,
    FlowsElementaryCategoryVariant62,
    FlowsElementaryCategoryVariant63,
    FlowsElementaryCategoryVariant64,
]
