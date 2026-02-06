"""
Convert FastAPI's OpenAPI 3.1 spec to Swagger 2.0 for Power Apps custom connectors.

Power Apps custom connectors only accept Swagger 2.0 (OpenAPI 2.0).
FastAPI generates OpenAPI 3.1, which uses features like anyOf for Optional
fields that Power Apps cannot parse.

Usage:
    uv run python scripts/convert_openapi_to_swagger.py

Reads from the running server at http://localhost:8000/openapi.json
and writes swagger2.json to the project root.
"""
from __future__ import annotations

import json
import sys
import urllib.request


def _fix_ref(ref: str) -> str:
    """Convert #/components/schemas/X to #/definitions/X."""
    return ref.replace("#/components/schemas/", "#/definitions/")


def convert_schema_property(prop: dict) -> dict:
    """Convert a single schema property from OpenAPI 3.1 to Swagger 2.0."""
    # Handle anyOf (used by Pydantic for Optional fields)
    if "anyOf" in prop:
        # Pick the first non-null type
        for variant in prop["anyOf"]:
            if variant.get("type") != "null":
                result = dict(variant)
                if "$ref" in result:
                    result["$ref"] = _fix_ref(result["$ref"])
                # Preserve title and default from parent
                if "title" in prop:
                    result["title"] = prop["title"]
                if "default" in prop:
                    result["default"] = prop["default"]
                return result
        # All variants are null — fallback to string
        return {"type": "string", "x-nullable": True}

    # Handle $ref
    if "$ref" in prop:
        return {"$ref": _fix_ref(prop["$ref"])}

    # Handle arrays
    if prop.get("type") == "array" and "items" in prop:
        result = dict(prop)
        result["items"] = convert_schema_property(prop["items"])
        return result

    return prop


def convert_schema(schema: dict) -> dict:
    """Convert a schema definition from OpenAPI 3.1 to Swagger 2.0."""
    result = {}

    if "type" in schema:
        result["type"] = schema["type"]
    if "title" in schema:
        result["title"] = schema["title"]
    if "description" in schema:
        result["description"] = schema["description"]
    if "default" in schema:
        result["default"] = schema["default"]
    if "enum" in schema:
        result["enum"] = schema["enum"]

    # Convert properties
    if "properties" in schema:
        result["properties"] = {}
        for name, prop in schema["properties"].items():
            result["properties"][name] = convert_schema_property(prop)

    if "required" in schema:
        result["required"] = schema["required"]

    if "items" in schema:
        result["items"] = convert_schema_property(schema["items"])

    return result


def convert_openapi3_to_swagger2(spec: dict, host: str = "localhost:8000") -> dict:
    """Convert a full OpenAPI 3.1 spec to Swagger 2.0."""
    swagger = {
        "swagger": "2.0",
        "info": spec.get("info", {}),
        "host": host,
        "basePath": "/",
        "schemes": ["https", "http"],
        "consumes": ["application/json"],
        "produces": ["application/json"],
        "paths": {},
        "definitions": {},
    }

    # Convert schemas -> definitions
    schemas = spec.get("components", {}).get("schemas", {})
    for name, schema in schemas.items():
        swagger["definitions"][name] = convert_schema(schema)

    # Convert paths
    for path, methods in spec.get("paths", {}).items():
        swagger["paths"][path] = {}
        for method, operation in methods.items():
            if method in ("get", "post", "put", "delete", "patch"):
                swagger_op = {
                    "operationId": operation.get("operationId", ""),
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                    "tags": operation.get("tags", []),
                    "parameters": [],
                    "responses": {},
                }

                # Add ngrok-skip-browser-warning header for all operations
                # Use boolean type with True default for Power Apps compatibility
                swagger_op["parameters"].append({
                    "in": "header",
                    "name": "ngrok-skip-browser-warning",
                    "type": "boolean",
                    "default": True,
                    "required": True,
                    "x-ms-visibility": "internal",
                })

                # Convert requestBody -> parameters (body)
                request_body = operation.get("requestBody")
                if request_body:
                    content = request_body.get("content", {})
                    json_content = content.get("application/json", {})
                    schema_ref = json_content.get("schema", {})
                    swagger_op["parameters"].append({
                        "in": "body",
                        "name": "body",
                        "required": request_body.get("required", False),
                        "schema": _convert_ref(schema_ref),
                    })

                # Convert responses
                for status, resp in operation.get("responses", {}).items():
                    swagger_resp = {"description": resp.get("description", "")}
                    content = resp.get("content", {})
                    json_content = content.get("application/json", {})
                    if "schema" in json_content:
                        swagger_resp["schema"] = _convert_ref(json_content["schema"])
                    swagger_op["responses"][status] = swagger_resp

                swagger["paths"][path][method] = swagger_op

    return swagger


def _convert_ref(schema: dict) -> dict:
    """Convert $ref from #/components/schemas/ to #/definitions/."""
    if "$ref" in schema:
        ref = schema["$ref"].replace("#/components/schemas/", "#/definitions/")
        return {"$ref": ref}
    return schema


def main():
    url = "http://localhost:8000/openapi.json"
    host = "localhost:8000"

    if len(sys.argv) > 1:
        host = sys.argv[1]

    print(f"Fetching OpenAPI spec from {url}...")
    try:
        with urllib.request.urlopen(url) as resp:
            spec = json.loads(resp.read())
    except Exception as e:
        print(f"ERROR: Could not fetch {url}: {e}")
        print("Make sure the API server is running: uv run uvicorn api.main:app --port 8000")
        sys.exit(1)

    print(f"Converting OpenAPI {spec.get('openapi', '?')} -> Swagger 2.0...")
    swagger = convert_openapi3_to_swagger2(spec, host=host)

    output_path = "swagger2.json"
    with open(output_path, "w") as f:
        json.dump(swagger, f, indent=2)

    print(f"Written to {output_path}")
    print(f"  Definitions: {list(swagger['definitions'].keys())}")
    print(f"  Paths: {list(swagger['paths'].keys())}")
    print()
    print("Next: Import swagger2.json into Power Apps custom connector")


if __name__ == "__main__":
    main()
