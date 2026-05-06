#!/usr/bin/env python3
"""
Compute coverage and test metrics from a Newman run report + OpenAPI spec.

Coverage = % of endpoints in openapi.json that have at least one test
in the Postman collection.
"""
import argparse
import json
import re
from pathlib import Path


def extract_endpoints_from_openapi(openapi_path: Path) -> set[str]:
    """Returns set of 'METHOD /path' strings from openapi.json."""
    spec = json.loads(openapi_path.read_text())
    endpoints = set()
    for path, methods in spec.get("paths", {}).items():
        for method in methods.keys():
            if method.lower() in {"get", "post", "put", "patch", "delete"}:
                endpoints.add(f"{method.upper()} {path}")
    return endpoints


def extract_endpoints_from_collection(collection_path: Path) -> set[str]:
    """Returns set of 'METHOD /path' strings tested by the collection."""
    coll = json.loads(collection_path.read_text())
    endpoints = set()

    def walk(items):
        for item in items:
            if "item" in item:
                walk(item["item"])
            req = item.get("request")
            if req:
                method = req.get("method", "GET").upper()
                url_obj = req.get("url", {})
                # url can be string or object
                if isinstance(url_obj, str):
                    url = url_obj
                else:
                    url = url_obj.get("raw", "")
                # Strip baseUrl variable, query string, and convert :id / {{var}} to {param}
                path = re.sub(r"^https?://[^/]+", "", url)
                path = re.sub(r"^\{\{baseUrl\}\}", "", path)
                path = path.split("?")[0]
                # Replace {{var}} placeholders with {var}-like param markers
                path = re.sub(r"\{\{(\w+)\}\}", r"{\1}", path)
                # Normalize :param -> {param}
                path = re.sub(r":(\w+)", r"{\1}", path)
                if path:
                    endpoints.add(f"{method} {path}")

    walk(coll.get("item", []))
    return endpoints


def normalize(endpoint: str) -> str:
    """Normalize for comparison: collapse {anything} to {param}."""
    method, path = endpoint.split(" ", 1)
    path = re.sub(r"\{[^}]+\}", "{param}", path)
    return f"{method} {path}"


def compute(newman_path: Path, openapi_path: Path, collection_path: Path) -> dict:
    spec_endpoints = extract_endpoints_from_openapi(openapi_path)
    coll_endpoints = extract_endpoints_from_collection(collection_path)

    spec_norm = {normalize(e): e for e in spec_endpoints}
    coll_norm = {normalize(e): e for e in coll_endpoints}

    covered = set(spec_norm.keys()) & set(coll_norm.keys())
    uncovered = set(spec_norm.keys()) - set(coll_norm.keys())

    coverage_pct = round(100 * len(covered) / max(len(spec_norm), 1), 1)

    # Newman stats
    newman_stats = {"total": 0, "passed": 0, "failed": 0, "duration_ms": 0}
    if newman_path.exists():
        newman = json.loads(newman_path.read_text())
        run = newman.get("run", {})
        stats = run.get("stats", {})
        assertions = stats.get("assertions", {})
        newman_stats["total"] = assertions.get("total", 0)
        newman_stats["failed"] = assertions.get("failed", 0)
        newman_stats["passed"] = newman_stats["total"] - newman_stats["failed"]
        timings = run.get("timings", {})
        newman_stats["duration_ms"] = int(timings.get("completed", 0) - timings.get("started", 0))

    pass_rate = round(100 * newman_stats["passed"] / max(newman_stats["total"], 1), 1)

    return {
        "coverage": {
            "pct": coverage_pct,
            "covered": len(covered),
            "total_endpoints": len(spec_norm),
            "covered_endpoints": sorted(spec_norm[k] for k in covered),
            "uncovered_endpoints": sorted(spec_norm[k] for k in uncovered),
        },
        "newman": {
            **newman_stats,
            "pass_rate_pct": pass_rate,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--newman-report", required=True)
    parser.add_argument("--openapi", required=True)
    parser.add_argument("--collection", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    metrics = compute(
        Path(args.newman_report),
        Path(args.openapi),
        Path(args.collection),
    )
    Path(args.output).write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
