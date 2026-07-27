from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import fastjsonschema
import pytest

from tidas_sdk import create_flow
from tidas_sdk.core.base import (
    _compile_fast_jsonschema_definition,
    _get_jsonschema_validator,
)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_payload() -> dict[str, object]:
    return json.loads(
        (FIXTURES_DIR / "flow-validation-parity.json").read_text(encoding="utf-8")
    )


def _payload_with_required_name_fields() -> dict[str, object]:
    payload = deepcopy(_load_payload())
    name = payload["flowDataSet"]["flowInformation"]["dataSetInformation"]["name"]
    name["treatmentStandardsRoutes"] = [
        {"@xml:lang": "en", "#text": "tar, syngas, char"}
    ]
    name["mixAndLocationTypes"] = [{"@xml:lang": "en", "#text": "at plant"}]
    return payload


def _payload_with_invalid_cas_number() -> dict[str, object]:
    payload = _payload_with_required_name_fields()
    data_set_info = payload["flowDataSet"]["flowInformation"]["dataSetInformation"]
    data_set_info["CASNumber"] = "64-17-6"
    return payload


def _valid_type_aware_name_payload(flow_type: str) -> dict[str, object]:
    payload = _load_payload()
    data_set = payload["flowDataSet"]
    data_set["modellingAndValidation"]["LCIMethod"]["typeOfDataSet"] = flow_type
    info = data_set["flowInformation"]["dataSetInformation"]
    info["name"]["baseName"][0]["#text"] = "Production from pyrolysis"
    info["common:synonyms"][0]["#text"] = "tar; syngas; char"
    return payload


def test_flow_pydantic_validation_rejects_missing_required_name_fields() -> None:
    entity = create_flow(_valid_type_aware_name_payload("Product flow"))

    assert entity.validate(mode="pydantic") is False

    error = entity.last_validation_error()
    assert error is not None

    rendered = str(error)
    assert (
        "treatmentStandardsRoutes" in rendered
        or "treatment_standards_routes" in rendered
    )
    assert "mixAndLocationTypes" in rendered or "mix_and_location_types" in rendered


def test_elementary_flow_pydantic_validation_allows_name_without_qualifiers() -> None:
    entity = create_flow(_valid_type_aware_name_payload("Elementary flow"))

    assert entity.validate(mode="pydantic") is True


@pytest.mark.parametrize("flow_type", ["Product flow", "Waste flow", "Other flow"])
def test_non_elementary_flow_pydantic_validation_requires_name_qualifiers(
    flow_type: str,
) -> None:
    entity = create_flow(_valid_type_aware_name_payload(flow_type))

    assert entity.validate(mode="pydantic") is False
    error = entity.last_validation_error()
    assert error is not None
    rendered = str(error)
    assert "treatmentStandardsRoutes" in rendered
    assert "mixAndLocationTypes" in rendered


def test_flow_pydantic_validation_rejects_invalid_localized_text() -> None:
    entity = create_flow(_payload_with_required_name_fields())

    assert entity.validate(mode="pydantic") is False

    error = entity.last_validation_error()
    assert error is not None
    assert "must not contain Chinese characters" in str(error)


def test_flow_jsonschema_validation_returns_validation_errors_not_execution_errors() -> (
    None
):
    entity = create_flow(_load_payload())

    assert entity.validate(mode="jsonschema") is False

    errors = entity.jsonschema_errors()
    assert errors
    assert all(
        "Schema validation failed to execute" not in message for message in errors
    )
    assert all("None is not of type 'string'" not in message for message in errors)
    assert all("datetime.datetime" not in message for message in errors)
    assert any("treatmentStandardsRoutes" in message for message in errors)
    assert any("mixAndLocationTypes" in message for message in errors)
    assert any("common:synonyms" in message for message in errors)


def test_flow_jsonschema_validation_rejects_invalid_cas_check_digit() -> None:
    entity = create_flow(_payload_with_invalid_cas_number())

    assert entity.validate(mode="jsonschema") is False

    errors = entity.jsonschema_errors()
    assert errors
    assert any("CASNumber" in message and "cas-number" in message for message in errors)


def test_flow_jsonschema_validator_is_cached_with_fast_path() -> None:
    validator = _get_jsonschema_validator("tidas_flows.json")

    assert validator is _get_jsonschema_validator("tidas_flows.json")
    assert validator.fast_validator is not None


def test_fast_jsonschema_validation_supports_refs_and_cas_format() -> None:
    validator = _compile_fast_jsonschema_definition(
        "test_schema.json",
        {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"cas": {"$ref": "tidas_data_types.json#/$defs/CASNumber"}},
            "required": ["cas"],
        },
    )

    assert validator({"cas": "64-17-5"}) == {"cas": "64-17-5"}

    with pytest.raises(fastjsonschema.JsonSchemaValueException) as exc_info:
        validator({"cas": "64-17-6"})

    assert exc_info.value.rule == "format"


def test_fast_jsonschema_validation_does_not_apply_defaults() -> None:
    validator = _compile_fast_jsonschema_definition(
        "test_defaults.json",
        {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"name": {"type": "string", "default": "generated"}},
        },
    )
    payload: dict[str, object] = {}

    assert validator(payload) == {}
    assert payload == {}
