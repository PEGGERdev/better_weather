from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND_MODELS = ROOT / "backend" / "data" / "models.py"
BACKEND_BINDINGS = ROOT / "backend" / "app" / "bindings.py"
OUTPUT = ROOT / "frontend" / "src" / "api" / "generated" / "backendContract.ts"


@dataclass(frozen=True)
class FieldDef:
    name: str
    ts_type: str
    optional: bool


def _literal_ts(annotation: ast.Subscript) -> str:
    values = annotation.slice
    if isinstance(values, ast.Tuple):
        items = values.elts
    else:
        items = [values]

    out: list[str] = []
    for item in items:
        if isinstance(item, ast.Constant):
            out.append(repr(item.value))
        else:
            out.append("'UNKNOWN'")
    return " | ".join(out)


def _annotation_to_ts(annotation: ast.expr) -> tuple[str, bool]:
    if isinstance(annotation, ast.Name):
        if annotation.id in {"float", "int"}:
            return "number", False
        if annotation.id == "str":
            return "string", False
        if annotation.id == "datetime":
            return "string", False
        return "unknown", False

    if isinstance(annotation, ast.Subscript) and isinstance(annotation.value, ast.Name):
        base = annotation.value.id
        if base == "Optional":
            inner = annotation.slice
            ts_type, _ = _annotation_to_ts(inner)
            return ts_type, True
        if base == "Literal":
            return _literal_ts(annotation), False

    return "unknown", False


def _class_collection(node: ast.ClassDef) -> str | None:
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        if not isinstance(decorator.func, ast.Name) or decorator.func.id != "mongo_entity":
            continue
        for keyword in decorator.keywords:
            if keyword.arg == "collection" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                return keyword.value.value
    return None


def _binding_collections(source: str) -> list[str]:
    tree = ast.parse(source)
    collections: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "EntityDefinition":
            continue
        for keyword in node.keywords:
            if keyword.arg == "collection" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                collections.append(keyword.value.value)
    return collections


def _class_fields(node: ast.ClassDef) -> list[FieldDef]:
    out: list[FieldDef] = []
    for statement in node.body:
        if not isinstance(statement, ast.AnnAssign):
            continue
        if not isinstance(statement.target, ast.Name):
            continue
        ts_type, optional = _annotation_to_ts(statement.annotation)
        out.append(FieldDef(name=statement.target.id, ts_type=ts_type, optional=optional))
    return out


def _parse_models(source: str) -> tuple[dict[str, list[FieldDef]], list[str]]:
    tree = ast.parse(source)
    models: dict[str, list[FieldDef]] = {}
    collections: list[str] = []

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue

        is_base_model = any(isinstance(base, ast.Name) and base.id == "BaseModel" for base in node.bases)
        if not is_base_model:
            continue

        models[node.name] = _class_fields(node)
        collection = _class_collection(node)
        if collection:
            collections.append(collection)

    return models, collections


def _validate(models: dict[str, list[FieldDef]], collections: list[str]) -> None:
    required = {
        "Weather": {"temp", "pressure", "light", "winds", "winddir", "rain", "humidity", "time"},
        "OSSD": {"time", "lichtgitterNr", "ossdNr", "ossdStatus"},
        "WitterungsstationPyState": {"time", "state"},
    }

    for model_name, fields in required.items():
        if model_name not in models:
            raise RuntimeError(f"Missing required model in backend/data/models.py: {model_name}")
        present = {field.name for field in models[model_name]}
        missing = sorted(fields - present)
        if missing:
            raise RuntimeError(f"Model {model_name} missing required fields: {', '.join(missing)}")

    required_collections = {"weather", "ossd", "witterungsstation_py_state"}
    missing_collections = sorted(required_collections - set(collections))
    if missing_collections:
        raise RuntimeError(
            "Missing required @mongo_entity collections: " + ", ".join(missing_collections)
        )


def _render_interface(name: str, fields: list[FieldDef]) -> str:
    lines = [f"export interface {name} {{", "  _id?: string"]
    for field in fields:
        key = f"{field.name}{'?' if field.optional and field.name != 'time' else ''}"
        value = "string" if field.name == "time" else field.ts_type
        lines.append(f"  {key}: {value}")
    lines.append("}")
    return "\n".join(lines)


def main() -> None:
    source = BACKEND_MODELS.read_text(encoding="utf-8")
    binding_source = BACKEND_BINDINGS.read_text(encoding="utf-8")
    models, collections = _parse_models(source)
    if not collections:
        collections = _binding_collections(binding_source)
    _validate(models, collections)

    weather_fields = models["Weather"]
    ossd_fields = models["OSSD"]
    state_fields = models["WitterungsstationPyState"]

    ossd_status = "'E' | 'O'"
    for field in ossd_fields:
        if field.name == "ossdStatus" and "|" in field.ts_type:
            ossd_status = field.ts_type
            break

    route_lines = ["export const BACKEND_ROUTES = {"]
    for collection in sorted(set(collections)):
        route_lines.append(f"  {collection.upper()}: '/{collection}/',")
    route_lines.append("} as const")

    output = "\n".join(
        [
            "// AUTO-GENERATED FILE. DO NOT EDIT.",
            "// Source: backend/data/models.py",
            "",
            f"export type BackendOssdStatus = {ossd_status}",
            "",
            _render_interface("BackendWeatherRecord", weather_fields),
            "",
            _render_interface("BackendInterruptRecord", ossd_fields),
            "",
            _render_interface("BackendWitterungsstationPyStateRecord", state_fields),
            "",
            *route_lines,
            "",
        ]
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(output, encoding="utf-8")
    print(f"Generated {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
