#!/usr/bin/env python3
"""
Fine-grained JSON Schema -> Pydantic generator.

Compared to off-the-shelf tools this script gives us the levers required for:
    * consistent naming/alias handling across the SDK
    * automatic MultiLangList wiring
    * incremental evolution as the schema surface grows
"""

from __future__ import annotations

import argparse
import json
import keyword
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

# Ensure the SDK sources are importable when running the script directly.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "sdks/python/src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


LOCALIZED_TEXT_MODEL_NAMES = {
    "LocalizedTextItem",
    "LocalizedText500Item",
    "LocalizedText1000Item",
}
GENERIC_MULTILANG_REF_NAMES = {
    "StringMultiLang",
    "STMultiLang",
    "FTMultiLang",
}
CHINESE_CHARACTER_PATTERN = r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]"
FLOW_NAME_CONDITIONAL_FIELDS = {
    "treatmentStandardsRoutes",
    "mixAndLocationTypes",
}
FLOW_NAME_MODEL_NAME = "FlowInformationDataSetInformationName"
FLOW_DATA_SET_MODEL_NAME = "FlowsFlowDataSet"


@dataclass
class GeneratorConfig:
    schemas_dir: Path
    output_dir: Path


@dataclass
class FieldDef:
    name: str
    alias: str
    type_hint: str
    required: bool
    default: str | None = None
    default_factory: str | None = None
    description: str | None = None
    constraints: dict[str, str] = field(default_factory=dict)


@dataclass
class ModelDef:
    name: str
    description: str | None
    fields: list[FieldDef] = field(default_factory=list)
    base_class: str | None = None


@dataclass
class ModuleArtifact:
    models: list[ModelDef]
    typing_imports: set[str]
    needs_multilang: bool
    warnings: list[str]
    standard_imports: set[str]
    scalar_definitions_pre: list[ScalarInfo]
    scalar_definitions_post: list[ScalarInfo]


@dataclass
class ScalarInfo:
    base_type: str
    constraints: dict[str, str] = field(default_factory=dict)
    description: str | None = None
    alias: str | None = None
    needs_multilang: bool = False
    typing_imports: set[str] = field(default_factory=set)
    standard_imports: set[str] = field(default_factory=set)
    definition: str | None = None
    post_definition: bool = False


class SchemaGenerator:
    def __init__(self, config: GeneratorConfig) -> None:
        self.config = config
        self.generated_index: list[tuple[str, list[str]]] = []
        self.schema_cache_dir = self.config.output_dir.parent / "schemas"
        self.global_scalars: dict[str, ScalarInfo] = {}

    def run(self) -> None:
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self.schema_cache_dir.mkdir(parents=True, exist_ok=True)
        schema_paths = sorted(
            self._iter_schema_files(),
            key=lambda path: (path.stem != "tidas_data_types", path.name),
        )
        for schema_path in schema_paths:
            module_name = schema_path.stem
            artifact = self._build_artifact(schema_path, module_name)
            output = self._render_module(schema_path.name, artifact)
            target_path = self.config.output_dir / f"{module_name}.py"
            target_path.write_text(output, encoding="utf-8")
            export_names = [model.name for model in artifact.models]
            export_names.extend(
                scalar.alias
                for scalar in artifact.scalar_definitions_pre
                + artifact.scalar_definitions_post
                if scalar.alias
            )
            self.generated_index.append((module_name, export_names))
            print(
                f"✓ Generated {target_path.relative_to(self.config.output_dir.parent)}"
            )
            for warning in artifact.warnings:
                print(f"  ⚠ {warning}")
            self._copy_schema(schema_path)

        self._write_package_init()

    def _iter_schema_files(self) -> Iterable[Path]:
        return self.config.schemas_dir.glob("*.json")

    def _build_artifact(self, schema_path: Path, module_name: str) -> ModuleArtifact:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        converter = SchemaConverter(
            schema,
            module_name,
            global_scalars=self.global_scalars,
        )
        return converter.convert()

    def _render_module(self, source_name: str, artifact: ModuleArtifact) -> str:
        needs_localized_text_validators = any(
            model.name in LOCALIZED_TEXT_MODEL_NAMES for model in artifact.models
        )
        needs_flow_name_condition_validator = any(
            model.name == FLOW_DATA_SET_MODEL_NAME for model in artifact.models
        )
        lines = [
            '"""',
            "Auto generated file. DO NOT EDIT.",
            f"Source: {source_name}",
            '"""',
            "from __future__ import annotations",
            "",
        ]

        if needs_localized_text_validators:
            lines.append("import re")
            lines.append("")

        if artifact.typing_imports:
            imports = ", ".join(sorted(artifact.typing_imports))
            lines.append(f"from typing import {imports}")
            lines.append("")

        pydantic_imports = ["Field"]
        if needs_localized_text_validators or needs_flow_name_condition_validator:
            pydantic_imports.append("model_validator")
        lines.append(f"from pydantic import {', '.join(pydantic_imports)}")
        lines.append("from tidas_sdk.core.base import TidasBaseModel")
        if artifact.needs_multilang:
            lines.append("from tidas_sdk.core.multilang import MultiLangList")
        lines.append("")
        for import_line in sorted(artifact.standard_imports):
            lines.append(import_line)
        if artifact.standard_imports:
            lines.append("")

        if needs_localized_text_validators:
            lines.append(
                f"CHINESE_CHARACTER_PATTERN = re.compile(r'{CHINESE_CHARACTER_PATTERN}')"
            )
            lines.append("")

        if artifact.scalar_definitions_pre:
            for scalar in artifact.scalar_definitions_pre:
                if scalar.description:
                    lines.append(f"# {scalar.description}")
                alias = scalar.alias or "ScalarAlias"
                definition = scalar.definition or f"{alias} = {scalar.base_type}"
                lines.append(definition)
            lines.append("")

        for model in artifact.models:
            lines.extend(self._render_model(model))
            lines.append("")

        if artifact.scalar_definitions_post:
            for scalar in artifact.scalar_definitions_post:
                if scalar.description:
                    lines.append(f"# {scalar.description}")
                alias = scalar.alias or "ScalarAlias"
                definition = scalar.definition or f"{alias} = {scalar.base_type}"
                lines.append(definition)
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def _render_model(cls, model: ModelDef) -> list[str]:
        base = model.base_class or "TidasBaseModel"
        lines: list[str] = [f"class {model.name}({base}):"]
        if model.description:
            safe_desc = sanitize_docstring(model.description)
            lines.append(f'    """{safe_desc}"""')

        if not model.fields:
            lines.append("    pass")
            return lines

        for field_def in model.fields:
            annotation = field_def.type_hint
            if (
                not field_def.required
                and field_def.default_factory is None
                and field_def.default in (None, "None")
                and "None" not in annotation
            ):
                annotation = f"{annotation} | None"

            field_args: list[str] = []
            if field_def.default_factory:
                field_args.append(f"default_factory={field_def.default_factory}")
            else:
                default_expr = field_def.default or "..."
                field_args.append(f"default={default_expr}")

            field_args.append(f"alias='{field_def.alias}'")
            if field_def.description:
                field_args.append(f"description={repr(field_def.description)}")
            for key, value in field_def.constraints.items():
                field_args.append(f"{key}={value}")

            field_line = (
                f"    {field_def.name}: {annotation} = Field({', '.join(field_args)})"
            )
            lines.append(field_line)

        validator_lines = cls._render_localized_text_validator(model.name)
        if validator_lines:
            lines.append("")
            lines.extend(validator_lines)
        flow_name_validator_lines = cls._render_flow_name_condition_validator(
            model.name
        )
        if flow_name_validator_lines:
            lines.append("")
            lines.extend(flow_name_validator_lines)

        return lines

    @staticmethod
    def _render_localized_text_validator(model_name: str) -> list[str]:
        if model_name not in LOCALIZED_TEXT_MODEL_NAMES:
            return []

        return [
            "    @model_validator(mode='after')",
            f"    def _validate_language_script(self) -> '{model_name}':",
            "        if self.xml_lang == 'zh' and not CHINESE_CHARACTER_PATTERN.search(self.text):",
            "            raise ValueError(\"@xml:lang value 'zh' must include at least one Chinese character\")",
            "        if self.xml_lang == 'en' and CHINESE_CHARACTER_PATTERN.search(self.text):",
            "            raise ValueError(\"@xml:lang value 'en' must not contain Chinese characters\")",
            "        return self",
        ]

    @staticmethod
    def _render_flow_name_condition_validator(model_name: str) -> list[str]:
        if model_name != FLOW_DATA_SET_MODEL_NAME:
            return []

        return [
            "    @model_validator(mode='after')",
            f"    def _validate_type_aware_flow_name(self) -> '{model_name}':",
            "        if self.modelling_and_validation.lci_method.type_of_data_set == 'Elementary flow':",
            "            return self",
            "        name = self.flow_information.data_set_information.name",
            "        missing = [",
            "            alias",
            "            for alias, value in (",
            "                ('treatmentStandardsRoutes', name.treatment_standards_routes),",
            "                ('mixAndLocationTypes', name.mix_and_location_types),",
            "            )",
            "            if value is None",
            "        ]",
            "        if missing:",
            "            raise ValueError(",
            "                'Flow name requires ' + ', '.join(missing)",
            "                + ' for Product, Waste, and Other flows'",
            "            )",
            "        return self",
        ]

    def _write_package_init(self) -> None:
        if not self.generated_index:
            return

        lines = [
            '"""Exports for auto-generated models."""',
            "from __future__ import annotations",
            "",
        ]
        exported_names: list[str] = []
        for module, names in self.generated_index:
            for name in names:
                lines.append(f"from .{module} import {name}")
            exported_names.extend(names)

        lines.append("")
        lines.append("__all__ = [")
        for name in exported_names:
            lines.append(f"    '{name}',")
        lines.append("]\n")

        target = self.config.output_dir / "__init__.py"
        target.write_text("\n".join(lines), encoding="utf-8")

    def _copy_schema(self, schema_path: Path) -> None:
        destination = self.schema_cache_dir / schema_path.name
        try:
            shutil.copy2(schema_path, destination)
        except FileNotFoundError:
            # schema may be intentionally absent from a partial source checkout
            pass


class SchemaConverter:
    """
    Convert a single JSON schema document into a ModuleArtifact.
    """

    def __init__(
        self,
        schema: dict[str, Any],
        module_name: str,
        *,
        global_scalars: dict[str, ScalarInfo] | None = None,
    ) -> None:
        self.schema = schema
        self.module_name = module_name
        self.models: dict[str, ModelDef] = {}
        self.model_order: list[str] = []
        self.ref_map: dict[str, str] = {}
        self.typing_imports: set[str] = set()
        self.needs_multilang = False
        self.warnings: list[str] = []
        self.standard_imports: set[str] = set()
        self.scalar_aliases: dict[str, ScalarInfo] = {}
        self.used_class_names: set[str] = set()
        self.global_scalars = global_scalars if global_scalars is not None else {}
        self.local_scalars: list[ScalarInfo] = []
        self.model_paths: dict[str, tuple[str, ...]] = {}

    def convert(self) -> ModuleArtifact:
        self._register_definitions()
        root_hint = self._derive_class_name(self.schema, self.module_name)
        union_scalar = self._handle_union_definition(root_hint, self.schema)
        if union_scalar:
            alias = normalize_alias_name(root_hint)
            union_scalar.alias = alias
            if not union_scalar.definition:
                union_scalar.definition = f"{alias} = {union_scalar.base_type}"
            self.local_scalars.append(union_scalar)
            self.scalar_aliases["#"] = union_scalar
            self.scalar_aliases[root_hint] = union_scalar
            self.scalar_aliases[self.module_name] = union_scalar
            module_ref = f"{self.module_name}.json"
            self.scalar_aliases[module_ref] = union_scalar
            self.global_scalars.setdefault(alias, union_scalar)
            self.global_scalars[self.module_name] = union_scalar
            self.global_scalars[module_ref] = union_scalar
            self.ref_map["#"] = alias
            for imp in union_scalar.typing_imports:
                if imp.startswith("from ") or imp.startswith("import "):
                    self.standard_imports.add(imp)
                else:
                    self.typing_imports.add(imp)
            for imp in union_scalar.standard_imports:
                self.standard_imports.add(imp)
        else:
            root_path = (root_hint,)
            root_class = self._ensure_model(self.schema, root_path, name_hint=root_hint)
            self.ref_map["#"] = root_class
        ordered_models = [self.models[name] for name in self.model_order]
        return ModuleArtifact(
            models=ordered_models,
            typing_imports=self.typing_imports,
            needs_multilang=self.needs_multilang,
            warnings=self.warnings,
            standard_imports=self.standard_imports,
            scalar_definitions_pre=[
                scalar for scalar in self.local_scalars if not scalar.post_definition
            ],
            scalar_definitions_post=[
                scalar for scalar in self.local_scalars if scalar.post_definition
            ],
        )

    def _register_definitions(self) -> None:
        for def_name, def_schema in self.schema.get("$defs", {}).items():
            pointer = f"#/$defs/{def_name}"
            extension_scalar = self._handle_extension_container_scalar(
                def_name, def_schema
            )
            if extension_scalar:
                self._register_scalar(def_name, pointer, extension_scalar)
                continue
            union_scalar = self._handle_union_definition(def_name, def_schema)
            if union_scalar:
                self._register_scalar(def_name, pointer, union_scalar)
                continue
            scalar = self._infer_scalar(def_schema)
            if scalar:
                self._register_scalar(def_name, pointer, scalar)
                continue
            alias_tokens = (def_name,)
            class_name = self._ensure_model(
                def_schema, alias_tokens, name_hint=def_name
            )
            self.ref_map[pointer] = class_name

    def _ensure_model(
        self,
        schema: dict[str, Any],
        path_tokens: tuple[str, ...],
        *,
        name_hint: str | None = None,
    ) -> str:
        class_name = self._compose_class_name(path_tokens, name_hint=name_hint)
        if class_name in self.models:
            return class_name

        model = self._build_model(class_name, schema, path_tokens)
        self.models[class_name] = model
        self.model_order.append(class_name)
        self.model_paths[class_name] = path_tokens
        return class_name

    def _build_model(
        self,
        class_name: str,
        schema: dict[str, Any],
        path_tokens: tuple[str, ...],
    ) -> ModelDef:
        normalized = self._normalize_object_schema(schema)
        properties = normalized["properties"]
        required = normalized["required"]
        description = normalized["description"]
        base_class = normalized["base_class"]

        fields: list[FieldDef] = []
        for prop_name, prop_schema in properties.items():
            is_required = prop_name in required
            field = self._build_field(
                class_name, path_tokens, prop_name, prop_schema, is_required
            )
            fields.append(field)

        return ModelDef(
            name=class_name,
            description=description,
            fields=fields,
            base_class=base_class,
        )

    def _build_field(
        self,
        parent_class: str,
        parent_path: tuple[str, ...],
        prop_name: str,
        prop_schema: dict[str, Any],
        is_required: bool,
    ) -> FieldDef:
        field_name = to_field_name(prop_name)

        alias = prop_name
        description = prop_schema.get("description")

        current_parent_path = parent_path
        if not current_parent_path:
            current_parent_path = self.model_paths.get(parent_class, tuple())

        is_conditionally_required_flow_name = (
            self.module_name == "tidas_flows"
            and parent_class == FLOW_NAME_MODEL_NAME
            and prop_name in FLOW_NAME_CONDITIONAL_FIELDS
        )
        if self._is_multilang_container(prop_schema):
            self.needs_multilang = True
            type_hint = "MultiLangList"
            if is_required:
                default_factory = None
                default_value = "..."
            elif is_conditionally_required_flow_name:
                default_factory = None
                default_value = "None"
            else:
                default_factory = "MultiLangList"
                default_value = None
        else:
            type_hint = self._determine_type(
                current_parent_path, prop_name, prop_schema
            )
            default_factory = self._default_factory(prop_schema)
            default_value = self._default_value(
                prop_schema, is_required, default_factory
            )

        constraints = self._collect_constraints(prop_schema)

        return FieldDef(
            name=field_name,
            alias=alias,
            type_hint=type_hint,
            required=is_required,
            default_factory=default_factory,
            default=default_value,
            description=description,
            constraints=constraints,
        )

    def _default_factory(self, schema: dict[str, Any]) -> str | None:
        type_name = schema.get("type")
        if self._is_multilang_container(schema):
            return "MultiLangList"
        if type_name == "array":
            return "list"
        if type_name == "object" and schema.get("properties"):
            return (
                None  # prefer nested model default None unless schema supplies default
            )
        if isinstance(schema.get("default"), (list, dict)):
            self.warnings.append(
                f"{self.module_name}: skipped mutable default for {schema.get('title', 'field')}"
            )
        return None

    def _default_value(
        self,
        schema: dict[str, Any],
        is_required: bool,
        default_factory: str | None,
    ) -> str | None:
        if default_factory:
            return None
        if "default" in schema and not isinstance(schema["default"], (dict, list)):
            return repr(schema["default"])
        return "..." if is_required else "None"

    def _determine_type(
        self,
        parent_path: tuple[str, ...],
        prop_name: str,
        schema: dict[str, Any] | list[Any] | str,
        qualifier: str | None = None,
    ) -> str:
        if isinstance(schema, list):
            option_types = {
                self._determine_type(
                    parent_path, prop_name, option, qualifier=f"option{i}"
                )
                for i, option in enumerate(schema)
                if isinstance(option, (dict, list))
            }
            if option_types:
                return " | ".join(sorted(option_types))
            self.typing_imports.add("Any")
            return "Any"

        if not isinstance(schema, dict):
            self.typing_imports.add("Any")
            return "Any"

        fmt = schema.get("format")
        if fmt == "date-time":
            self.standard_imports.add("from datetime import datetime")
            return "datetime"
        if fmt == "date":
            self.standard_imports.add("from datetime import date")
            return "date"
        if fmt == "time":
            self.standard_imports.add("from datetime import time")
            return "time"
        if fmt == "uuid":
            self.standard_imports.add("from uuid import UUID")
            return "UUID"

        if "$ref" in schema:
            return self._resolve_ref(schema["$ref"])

        if "const" in schema:
            value = schema["const"]
            self.typing_imports.add("Literal")
            return f"Literal[{repr(value)}]"

        for key in ("oneOf", "anyOf"):
            if key in schema:
                options = schema[key]
                types = {
                    self._determine_type(
                        parent_path + (prop_name,),
                        prop_name,
                        option,
                        qualifier=f"option{i}",
                    )
                    for i, option in enumerate(options)
                }
                return " | ".join(sorted(types))

        if "enum" in schema:
            self.typing_imports.add("Literal")
            literals = ", ".join(repr(value) for value in schema["enum"])
            return f"Literal[{literals}]"

        if "allOf" in schema:
            inline_schema: dict[str, Any] | None = None
            ref_types: list[str] = []
            for entry in schema["allOf"]:
                if isinstance(entry, dict):
                    if "$ref" in entry:
                        ref_types.append(self._resolve_ref(entry["$ref"]))
                    elif entry.get("type") == "object":
                        inline_schema = inline_schema or {}
                        inline_schema = self._merge_inline_schema(inline_schema, entry)
                    else:
                        # treat as constraint-only fragment, ignore
                        continue
            if inline_schema:
                if ref_types:
                    inline_schema = {**inline_schema, "$ref": ref_types[0]}
                new_path = parent_path + (prop_name,)
                return self._inline_model(new_path, inline_schema, qualifier=qualifier)
            if ref_types:
                return ref_types[0]
            # Fall back to schema without allOf (constraints only)
            reduced_schema = {k: v for k, v in schema.items() if k != "allOf"}
            if reduced_schema:
                return self._determine_type(
                    parent_path, prop_name, reduced_schema, qualifier=qualifier
                )
            self.warnings.append(
                f"{self.module_name}: unsupported allOf on {prop_name}, using Any"
            )
            self.typing_imports.add("Any")
            return "Any"

        type_name = schema.get("type")
        if type_name is None:
            if isinstance(schema.get("properties"), dict):
                type_name = "object"
            elif "items" in schema:
                type_name = "array"
        if isinstance(type_name, list):
            non_null = [t for t in type_name if t != "null"]
            if not non_null:
                self.typing_imports.add("Any")
                return "Any"
            schema = {**schema, "type": non_null[0]}
            return f"{self._determine_type(parent_path, prop_name, schema)} | None"

        if type_name == "array":
            item_schema = schema.get("items", {})
            item_type = self._determine_type(
                parent_path + (prop_name,), "item", item_schema
            )
            return f"list[{item_type}]"

        if type_name == "object":
            if schema.get("properties"):
                return self._inline_model(
                    parent_path + (prop_name,), schema, qualifier=qualifier
                )
            pattern_properties = schema.get("patternProperties")
            if isinstance(pattern_properties, dict) and pattern_properties:
                value_types = {
                    self._determine_type(
                        parent_path + (prop_name,), "value", value_schema
                    )
                    for value_schema in pattern_properties.values()
                    if isinstance(value_schema, dict)
                }
                if value_types:
                    return f"dict[str, {' | '.join(sorted(value_types))}]"
            additional = schema.get("additionalProperties")
            if isinstance(additional, dict):
                value_type = self._determine_type(
                    parent_path + (prop_name,), "value", additional
                )
                return f"dict[str, {value_type}]"
            self.typing_imports.add("Any")
            return "dict[str, Any]"

        return self._map_primitive(type_name)

    def _inline_model(
        self,
        path_tokens: tuple[str, ...],
        schema: dict[str, Any],
        qualifier: str | None = None,
    ) -> str:
        name_hint = path_tokens[-1] if path_tokens else None
        if qualifier:
            path_tokens = path_tokens + (qualifier,)
            name_hint = qualifier
        class_name = self._ensure_model(schema, path_tokens, name_hint=name_hint)
        return class_name

    def _map_primitive(self, type_name: str | None) -> str:
        mapping = {
            "string": "str",
            "number": "float",
            "integer": "int",
            "boolean": "bool",
        }
        if type_name in mapping:
            return mapping[type_name]
        self.typing_imports.add("Any")
        return "Any"

    def _resolve_ref(self, ref: str) -> str:
        scalar = self._lookup_scalar(ref)
        if scalar:
            if scalar.needs_multilang:
                self.needs_multilang = True
            for imp in scalar.typing_imports:
                if imp.startswith("from ") or imp.startswith("import "):
                    self.standard_imports.add(imp)
                else:
                    self.typing_imports.add(imp)
            for imp in scalar.standard_imports:
                self.standard_imports.add(imp)
            result = scalar.alias or scalar.base_type
            if self._needs_external_import(ref, result):
                module_name = self._module_name_from_ref(ref)
                if module_name:
                    self.standard_imports.add(f"from .{module_name} import {result}")
            return result

        if ref not in self.ref_map:
            target = ref.split("/")[-1]
            module_name = self._module_name_from_ref(ref)
            if module_name:
                alias_source = module_name
                if module_name.startswith("tidas_"):
                    alias_source = module_name.removeprefix("tidas_")
                alias = normalize_alias_name(alias_source)
                self.standard_imports.add(f"from .{module_name} import {alias}")
                self.ref_map[ref] = alias
            else:
                class_name = self._unique_class_name(to_pascal_case(target))
                self.ref_map[ref] = class_name
        return self.ref_map[ref]

    @staticmethod
    def _derive_class_name(schema: dict[str, Any], module_name: str) -> str:
        if "title" in schema:
            return to_pascal_case(schema["title"])
        stem = module_name
        if stem.startswith("tidas_"):
            stem = stem.removeprefix("tidas_")
        return to_pascal_case(stem)

    @staticmethod
    def _is_multilang_container(schema: dict[str, Any]) -> bool:
        if isinstance(schema, list):
            return any(
                SchemaConverter._is_multilang_container(item)
                for item in schema
                if isinstance(item, dict)
            )

        if SchemaConverter._is_generic_multilang_ref(schema.get("$ref", "")):
            return True

        title = schema.get("title", "")
        if isinstance(title, str) and title in GENERIC_MULTILANG_REF_NAMES:
            return True

        for key in ("anyOf", "oneOf"):
            variants = schema.get(key)
            if isinstance(variants, list):
                return any(
                    SchemaConverter._is_multilang_container(item)
                    or SchemaConverter._is_multilang_item(item)
                    for item in variants
                    if isinstance(item, dict)
                )

        if schema.get("type") == "array":
            items = schema.get("items", {})
            # items can be a schema or a list of schemas (tuples, anyOf style)
            if isinstance(items, list):
                return any(
                    SchemaConverter._is_multilang_container(item)
                    or SchemaConverter._is_multilang_item(item)
                    for item in items
                    if isinstance(item, dict)
                )
            return SchemaConverter._is_multilang_item(items)

        return False

    @staticmethod
    def _is_generic_multilang_ref(ref: str) -> bool:
        if not ref:
            return False
        return ref.split("/")[-1] in GENERIC_MULTILANG_REF_NAMES

    @staticmethod
    def _is_multilang_item(schema: dict[str, Any]) -> bool:
        if isinstance(schema, list):
            return any(
                SchemaConverter._is_multilang_item(item)
                for item in schema
                if isinstance(item, dict)
            )
        if not isinstance(schema, dict):
            return False

        if "$ref" in schema and schema["$ref"].endswith("LocalizedTextItem"):
            return True

        if "$ref" in schema and re.search(
            r"LocalizedText(?:\d+)?Item$", schema["$ref"]
        ):
            return True

        properties = schema.get("properties", {})
        return "@xml:lang" in properties and "#text" in properties

    def _normalize_object_schema(self, schema: Any) -> dict[str, Any]:
        """
        Merge object schemas by resolving allOf constructs and capture base classes.
        """
        properties: dict[str, Any] = {}
        required: set[str] = set()
        description: str | None = None
        base_class: str | None = None

        if not isinstance(schema, dict):
            return {
                "properties": properties,
                "required": required,
                "description": description,
                "base_class": base_class,
            }

        if isinstance(schema.get("description"), str):
            description = schema["description"]

        if "$ref" in schema:
            scalar = self._lookup_scalar(schema["$ref"])
            if scalar is None:
                candidate = self._resolve_ref(schema["$ref"])
                if candidate and candidate[0].isupper() and candidate.isidentifier():
                    base_class = candidate
                ref_schema = self._resolve_local_ref_schema(schema["$ref"])
                if ref_schema is not None:
                    normalized_ref = self._normalize_object_schema(ref_schema)
                    properties = self._merge_property_maps(
                        properties,
                        normalized_ref["properties"],
                    )
                    required |= normalized_ref["required"]
                    if not description:
                        description = normalized_ref["description"]
                    if normalized_ref["base_class"] and not base_class:
                        base_class = normalized_ref["base_class"]

        all_of = schema.get("allOf")
        if isinstance(all_of, list):
            for part in all_of:
                normalized = self._normalize_object_schema(part)
                properties = self._merge_property_maps(
                    properties,
                    normalized["properties"],
                )
                required |= normalized["required"]
                if not description:
                    description = normalized["description"]
                if normalized["base_class"] and not base_class:
                    base_class = normalized["base_class"]

        if "properties" in schema and isinstance(schema["properties"], dict):
            properties = self._merge_property_maps(properties, schema["properties"])

        required |= set(schema.get("required", []))

        return {
            "properties": properties,
            "required": required,
            "description": description,
            "base_class": base_class,
        }

    def _resolve_local_ref_schema(self, ref: str) -> dict[str, Any] | None:
        if not ref.startswith("#/$defs/"):
            return None

        ref_name = ref.split("/")[-1]
        defs = self.schema.get("$defs", {})
        resolved = defs.get(ref_name)
        return resolved if isinstance(resolved, dict) else None

    @staticmethod
    def _merge_property_schema(base: Any, new: Any) -> dict[str, Any]:
        if not isinstance(base, dict):
            return dict(new) if isinstance(new, dict) else {}
        if not isinstance(new, dict):
            return dict(base)

        merged = {**base, **new}

        if "properties" in base or "properties" in new:
            merged["properties"] = {
                **(base.get("properties", {}) or {}),
                **(new.get("properties", {}) or {}),
            }

        if "required" in base or "required" in new:
            merged["required"] = list(
                {
                    *(base.get("required", []) or []),
                    *(new.get("required", []) or []),
                }
            )

        if "not" in base and "not" in new:
            merged["not"] = {**base["not"], **new["not"]}

        return merged

    def _merge_property_maps(
        self,
        base: dict[str, Any],
        new: dict[str, Any],
    ) -> dict[str, Any]:
        merged = dict(base)
        for key, value in new.items():
            if key in merged:
                merged[key] = self._merge_property_schema(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _collect_constraints(self, schema: dict[str, Any]) -> dict[str, str]:
        constraints: dict[str, str] = {}
        if not isinstance(schema, dict):
            return constraints

        if "minimum" in schema:
            constraints["ge"] = repr(schema["minimum"])
        if "maximum" in schema:
            constraints["le"] = repr(schema["maximum"])
        if "exclusiveMinimum" in schema:
            constraints["gt"] = repr(schema["exclusiveMinimum"])
        if "exclusiveMaximum" in schema:
            constraints["lt"] = repr(schema["exclusiveMaximum"])
        if "minLength" in schema:
            constraints["min_length"] = repr(schema["minLength"])
        if "maxLength" in schema:
            constraints["max_length"] = repr(schema["maxLength"])
        if "pattern" in schema:
            pattern = schema["pattern"]
            if isinstance(pattern, str):
                constraints["pattern"] = repr(pattern)
        if "minItems" in schema:
            constraints["min_items"] = repr(schema["minItems"])
        if "maxItems" in schema:
            constraints["max_items"] = repr(schema["maxItems"])
        if "multipleOf" in schema:
            constraints["multiple_of"] = repr(schema["multipleOf"])

        return constraints

    @staticmethod
    def _handle_extension_container_scalar(
        name: str, schema: dict[str, Any]
    ) -> ScalarInfo | None:
        if name == "AnyXmlElement":
            return ScalarInfo(
                base_type="Any",
                description=schema.get("description"),
                typing_imports={"Any"},
            )
        if name == "CommonOther":
            definition = """_COMMON_OTHER_NAMESPACE_DECLARATION_PATTERN = re.compile(
    r'^@xmlns(:[A-Za-z_][A-Za-z0-9_.-]*)?$'
)
_COMMON_OTHER_EXTENSION_ELEMENT_PATTERN = re.compile(
    r'^(?!(common|xmlns):)([A-Za-z_][A-Za-z0-9_.-]*:)?[A-Za-z_][A-Za-z0-9_.-]*$'
)

def _validate_common_other(value: dict[str, AnyXmlElement]) -> dict[str, AnyXmlElement]:
    has_extension_element = False

    for key, entry_value in value.items():
        if _COMMON_OTHER_NAMESPACE_DECLARATION_PATTERN.fullmatch(key):
            if not isinstance(entry_value, str):
                raise ValueError("Namespace declarations in common:other must be strings")
            continue

        if _COMMON_OTHER_EXTENSION_ELEMENT_PATTERN.fullmatch(key):
            has_extension_element = True
            continue

        raise ValueError(
            "common:other entries must be namespace declarations or non-common extension elements"
        )

    if not has_extension_element:
        raise ValueError("common:other must include at least one non-common extension element")

    return value

CommonOther = Annotated[dict[str, AnyXmlElement], AfterValidator(_validate_common_other)]"""
            return ScalarInfo(
                base_type="dict[str, AnyXmlElement]",
                description=schema.get("description"),
                definition=definition,
                typing_imports={"Annotated"},
                standard_imports={"from pydantic import AfterValidator"},
            )
        return None

    def _handle_union_definition(
        self, name: str, schema: dict[str, Any]
    ) -> ScalarInfo | None:
        if not isinstance(schema, dict):
            return None
        for key in ("oneOf", "anyOf"):
            variants = schema.get(key)
            if not isinstance(variants, list):
                continue
            option_types: list[str] = []
            for index, option in enumerate(variants):
                if not isinstance(option, (dict, list)):
                    continue
                type_expr = self._determine_type(
                    (name,),
                    f"variant{index}",
                    option,
                    qualifier=f"variant{index}",
                )
                option_types.append(type_expr)
            if option_types:
                # Preserve order while removing duplicates
                seen: set[str] = set()
                ordered: list[str] = []
                for expr in option_types:
                    if expr not in seen:
                        seen.add(expr)
                        ordered.append(expr)
                literal_values: list[str] = []
                other_types: list[str] = []
                for expr in ordered:
                    if (
                        expr.startswith("Literal[")
                        and expr.endswith("]")
                        and "|" not in expr
                    ):
                        inner = expr[len("Literal[") : -1].strip()
                        if inner:
                            for value in inner.split(","):
                                cleaned = value.strip()
                                if cleaned:
                                    literal_values.append(cleaned)
                    else:
                        other_types.append(expr)
                if literal_values:
                    dedup_literal_values: list[str] = []
                    seen_literal: set[str] = set()
                    for value in literal_values:
                        if value not in seen_literal:
                            seen_literal.add(value)
                            dedup_literal_values.append(value)
                    combined_literal = f"Literal[{', '.join(dedup_literal_values)}]"
                    union_parts = [combined_literal, *other_types]
                else:
                    union_parts = ordered
                typing_imports: set[str] = set()
                if len(union_parts) == 1:
                    union_expr = union_parts[0]
                elif len(union_parts) <= 4:
                    union_expr = " | ".join(union_parts)
                else:
                    formatted = ",\n    ".join(union_parts)
                    union_expr = f"Union[\n    {formatted},\n]"
                    typing_imports.add("Union")
                scalar = ScalarInfo(
                    base_type=union_expr,
                    description=schema.get("description"),
                    post_definition=True,
                )
                if any("Literal[" in expr for expr in union_parts):
                    typing_imports.add("Literal")
                scalar.typing_imports.update(typing_imports)
                return scalar
        return None

    @staticmethod
    def _module_name_from_ref(ref: str) -> str | None:
        if ref.startswith("#"):
            return None
        if ".json" not in ref:
            return None
        module_part = ref.split("#", 1)[0]
        return Path(module_part).stem

    def _needs_external_import(self, ref: str, symbol: str) -> bool:
        if ref.startswith("#"):
            return False
        if not symbol or not symbol[0].isalpha():
            return False
        if not symbol.isidentifier():
            return False
        module_name = self._module_name_from_ref(ref)
        if not module_name or module_name == self.module_name:
            return False
        if symbol in {"Literal", "Annotated", "datetime", "date", "time"}:
            return False
        return True

    def _register_scalar(self, name: str, pointer: str, scalar: ScalarInfo) -> None:
        alias = normalize_alias_name(name)
        scalar.alias = alias
        if not scalar.definition:
            if scalar.constraints:
                args = ", ".join(f"{k}={v}" for k, v in scalar.constraints.items())
                cas_validator_import = "from tidas_sdk.core.cas_number import validate_cas_number_check_digit"
                if cas_validator_import in scalar.standard_imports:
                    scalar.definition = (
                        f"{alias} = Annotated[{scalar.base_type}, Field({args}), "
                        "AfterValidator(validate_cas_number_check_digit)]"
                    )
                    scalar.standard_imports.add("from pydantic import AfterValidator")
                else:
                    scalar.definition = (
                        f"{alias} = Annotated[{scalar.base_type}, Field({args})]"
                    )
                self.typing_imports.add("Annotated")
            else:
                scalar.definition = f"{alias} = {scalar.base_type}"

        self.scalar_aliases[pointer] = scalar
        self.scalar_aliases[name] = scalar
        self.global_scalars[name] = scalar
        self.global_scalars[pointer] = scalar
        if scalar.needs_multilang:
            self.needs_multilang = True
        for imp in scalar.typing_imports:
            if imp.startswith("from ") or imp.startswith("import "):
                self.standard_imports.add(imp)
            else:
                self.typing_imports.add(imp)
        for imp in scalar.standard_imports:
            self.standard_imports.add(imp)
        if pointer.startswith("#/$defs/") or name in self.schema.get("$defs", {}):
            self.local_scalars.append(scalar)
        self.ref_map[pointer] = scalar.alias or scalar.base_type

    def _lookup_scalar(self, ref: str) -> ScalarInfo | None:
        if ref in self.scalar_aliases:
            return self.scalar_aliases[ref]
        target = ref.split("/")[-1]
        if target in self.scalar_aliases:
            return self.scalar_aliases[target]
        if ref in self.global_scalars:
            return self.global_scalars[ref]
        if target in self.global_scalars:
            return self.global_scalars[target]
        return None

    def _infer_scalar(self, schema: Any) -> ScalarInfo | None:
        if not isinstance(schema, dict):
            return None
        if self._is_multilang_container(schema):
            return ScalarInfo(
                base_type="MultiLangList",
                needs_multilang=True,
                description=schema.get("description"),
            )
        if "$ref" in schema:
            ref_scalar = self._lookup_scalar(schema["$ref"])
            if ref_scalar:
                return ScalarInfo(
                    base_type=ref_scalar.alias or ref_scalar.base_type,
                    description=schema.get("description") or ref_scalar.description,
                    needs_multilang=ref_scalar.needs_multilang,
                    typing_imports=set(ref_scalar.typing_imports),
                    standard_imports=set(ref_scalar.standard_imports),
                )

        if "anyOf" in schema and isinstance(schema["anyOf"], list):
            options = [
                self._infer_scalar(option)
                for option in schema["anyOf"]
                if isinstance(option, (dict, list))
            ]
            options = [opt for opt in options if opt is not None]
            if options and all(
                (opt.alias or opt.base_type)
                == (options[0].alias or options[0].base_type)
                for opt in options
            ):
                combined_imports: set[str] = set()
                for opt in options:
                    combined_imports.update(opt.typing_imports)
                return ScalarInfo(
                    base_type=options[0].alias or options[0].base_type,
                    needs_multilang=any(opt.needs_multilang for opt in options),
                    typing_imports=combined_imports,
                    description=schema.get("description"),
                )
            return None

        if "enum" in schema and isinstance(schema["enum"], list):
            literals = ", ".join(repr(value) for value in schema["enum"])
            return ScalarInfo(
                base_type=f"Literal[{literals}]",
                typing_imports={"Literal"},
                description=schema.get("description"),
            )

        schema_type = schema.get("type")
        if schema_type == "string":
            fmt = schema.get("format")
            if fmt == "date-time":
                return ScalarInfo(
                    base_type="datetime",
                    standard_imports={"from datetime import datetime"},
                    description=schema.get("description"),
                )
            if fmt == "date":
                return ScalarInfo(
                    base_type="date",
                    standard_imports={"from datetime import date"},
                    description=schema.get("description"),
                )
            if fmt == "time":
                return ScalarInfo(
                    base_type="time",
                    standard_imports={"from datetime import time"},
                    description=schema.get("description"),
                )
            if fmt == "cas-number":
                constraints = self._collect_constraints(schema)
                return ScalarInfo(
                    base_type="str",
                    constraints=constraints,
                    standard_imports={
                        "from pydantic import AfterValidator",
                        "from tidas_sdk.core.cas_number import validate_cas_number_check_digit",
                    },
                    description=schema.get("description"),
                )
            constraints = self._collect_constraints(schema)
            return ScalarInfo(
                base_type="str",
                constraints=constraints,
                description=schema.get("description"),
            )
        if schema_type == "integer":
            constraints = self._collect_constraints(schema)
            return ScalarInfo(
                base_type="int",
                constraints=constraints,
                description=schema.get("description"),
            )
        if schema_type == "number":
            constraints = self._collect_constraints(schema)
            return ScalarInfo(
                base_type="float",
                constraints=constraints,
                description=schema.get("description"),
            )
        if schema_type == "boolean":
            return ScalarInfo(base_type="bool", description=schema.get("description"))

        return None

    def _compose_class_name(
        self,
        path_tokens: tuple[str, ...],
        name_hint: str | None = None,
    ) -> str:
        tokens = [to_pascal_case(token) for token in path_tokens if token]
        if not tokens and name_hint:
            tokens = [to_pascal_case(name_hint)]
        dedup: list[str] = []
        for token in tokens:
            if not dedup or dedup[-1] != token:
                dedup.append(token)
        candidate = "".join(dedup[-3:]) if dedup else "GeneratedModel"
        return self._unique_class_name(candidate)

    def _unique_class_name(self, candidate: str) -> str:
        if not candidate:
            candidate = "GeneratedModel"
        candidate = candidate[0].upper() + candidate[1:]
        max_length = 120
        if len(candidate) > max_length:
            tail = _split_camel(candidate)[-3:]
            shortened = "".join(token.capitalize() for token in tail)
            if shortened and len(shortened) <= max_length:
                candidate = shortened
            else:
                candidate = candidate[:max_length]
        base = candidate
        counter = 1
        while base in self.used_class_names:
            counter += 1
            base = f"{candidate}{counter}"
        self.used_class_names.add(base)
        return base

    @staticmethod
    def _merge_inline_schema(
        base: dict[str, Any], new: dict[str, Any]
    ) -> dict[str, Any]:
        merged = {**base}
        if "properties" in new:
            merged.setdefault("properties", {})
            merged["properties"].update(new["properties"])
        if "required" in new:
            merged.setdefault("required", [])
            merged["required"] = list({*merged["required"], *new["required"]})
        for key in ("description", "title"):
            if key in new and key not in merged:
                merged[key] = new[key]
        return merged


def _split_camel(value: str) -> list[str]:
    value = re.sub(r"[^0-9A-Za-z]+", " ", value)
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    tokens = [
        token for token in value.replace("@", " ").replace("#", " ").split() if token
    ]
    return tokens


def to_pascal_case(value: str) -> str:
    tokens = _split_camel(value)
    parts: list[str] = []
    for token in tokens:
        if token.isupper():
            parts.append(token)
        else:
            parts.append(token[0].upper() + token[1:].lower())
    return "".join(parts) or "GeneratedModel"


def to_field_name(value: str) -> str:
    tokens = _split_camel(value)
    if not tokens:
        return "field"
    parts = [tokens[0].lower()]
    for token in tokens[1:]:
        parts.append(token.lower())
    name = "_".join(parts)
    name = re.sub(r"__+", "_", name).strip("_")
    if not name:
        return "field"
    if keyword.iskeyword(name):
        name += "_"
    return name


def normalize_alias_name(value: str) -> str:
    if value.isupper():
        return value
    return to_pascal_case(value)


def sanitize_docstring(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return escaped


def parse_args() -> argparse.Namespace:
    script_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Generate Python SDK models from JSON Schema files."
    )
    parser.add_argument(
        "--schemas",
        type=Path,
        required=True,
        help="Directory containing *.json schema files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=script_root / "src/tidas_sdk/generated",
        help="Output directory for generated modules.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = GeneratorConfig(
        schemas_dir=args.schemas.resolve(),
        output_dir=args.output.resolve(),
    )
    generator = SchemaGenerator(config)
    generator.run()


if __name__ == "__main__":
    main()
