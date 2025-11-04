"""Lightweight jsonschema-compatible validator for tests."""
from __future__ import annotations

import re
from typing import Any

__all__ = ["ValidationError", "validate"]


class ValidationError(ValueError):
    """Exception raised when validation fails."""

    def __init__(self, message: str, path: tuple[Any, ...] | None = None) -> None:
        self.message = message
        self.path = path or ()
        super().__init__(self.__str__())

    def __str__(self) -> str:  # pragma: no cover - formatting helper
        if not self.path:
            return self.message
        joined = "/".join(str(p) for p in self.path)
        return f"{self.message} at {joined}"


def validate(instance: Any, schema: dict[str, Any]) -> None:
    """Validate *instance* against the provided *schema* subset."""

    _validate(instance, schema, path=())


def _validate(instance: Any, schema: dict[str, Any], path: tuple[Any, ...]) -> None:
    schema_type = schema.get("type")
    if schema_type is not None:
        _check_type(instance, schema_type, path)

    enum = schema.get("enum")
    if enum is not None and instance not in enum:
        raise ValidationError("Value not in enum", path)

    pattern = schema.get("pattern")
    if pattern is not None:
        if not isinstance(instance, str) or re.fullmatch(pattern, instance) is None:
            raise ValidationError("String does not match pattern", path)

    minimum = schema.get("minimum")
    if minimum is not None:
        if not _is_number(instance) or instance < minimum:
            raise ValidationError("Number below minimum", path)

    maximum = schema.get("maximum")
    if maximum is not None:
        if not _is_number(instance) or instance > maximum:
            raise ValidationError("Number above maximum", path)

    if schema.get("type") == "object":
        _validate_object(instance, schema, path)
    elif schema.get("type") == "array":
        _validate_array(instance, schema, path)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_type(instance: Any, schema_type: Any, path: tuple[Any, ...]) -> None:
    candidates = schema_type if isinstance(schema_type, list) else [schema_type]
    for candidate in candidates:
        if candidate == "object" and isinstance(instance, dict):
            return
        if candidate == "array" and isinstance(instance, list):
            return
        if candidate == "string" and isinstance(instance, str):
            return
        if candidate == "boolean" and isinstance(instance, bool):
            return
        if candidate == "integer" and isinstance(instance, int) and not isinstance(instance, bool):
            return
        if candidate == "number" and _is_number(instance):
            return
    raise ValidationError(f"Expected type {schema_type}", path)


def _validate_object(instance: Any, schema: dict[str, Any], path: tuple[Any, ...]) -> None:
    if not isinstance(instance, dict):
        raise ValidationError("Object expected", path)

    properties = schema.get("properties", {})
    required = schema.get("required", [])
    for key in required:
        if key not in instance:
            raise ValidationError(f"Missing required property '{key}'", path + (key,))

    additional = schema.get("additionalProperties", True)
    for key, value in instance.items():
        if key in properties:
            _validate(value, properties[key], path + (key,))
        elif isinstance(additional, dict):
            _validate(value, additional, path + (key,))
        elif additional is False:
            raise ValidationError(f"Additional property '{key}' not allowed", path + (key,))


def _validate_array(instance: Any, schema: dict[str, Any], path: tuple[Any, ...]) -> None:
    if not isinstance(instance, list):
        raise ValidationError("Array expected", path)

    min_items = schema.get("minItems")
    if min_items is not None and len(instance) < min_items:
        raise ValidationError("Array shorter than minItems", path)

    items_schema = schema.get("items")
    if isinstance(items_schema, dict):
        for index, item in enumerate(instance):
            _validate(item, items_schema, path + (index,))
    elif isinstance(items_schema, list):  # pragma: no cover - unused in tests
        for index, item_schema in enumerate(items_schema):
            if index < len(instance):
                _validate(instance[index], item_schema, path + (index,))

