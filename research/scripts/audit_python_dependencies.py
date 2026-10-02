"""Fail-closed installed-package audit; never installs or resolves dependencies.

Run with a separate pip-audit==2.10.1 virtualenv, for example:
    python research/scripts/audit_python_dependencies.py \
        --target-python .venv-ci/bin/python --auditor-python .venv-audit/bin/python

stdout is one JSON record, including inventory and unmodified subprocess output.
Exit 0 means both advisory queries passed the coverage checks, not zero risk.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


CPU_VERSION = "2.13.0+cpu"
BASE_VERSION = "2.13.0"
AUDITOR_VERSION = "2.10.1"
EXPECTED_SKIP = (
    "Dependency not found on PyPI and could not be audited: "
    f"torch ({CPU_VERSION})"
)
LIMITATION = (
    f"PyPI cannot audit the installed torch=={CPU_VERSION} CPU wheel directly. "
    f"The separate torch=={BASE_VERSION} query covers upstream version advisory "
    "metadata only; it does not establish binary-specific CPU-wheel coverage "
    "or absence of vulnerabilities. The installed-wheel skip is retained."
)
BASE_WARNINGS = {
    "WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged "
    "to fully hash their pinned dependencies",
    "WARNING:pip_audit._cli:Consider using a tool like `pip-compile`: "
    "https://pip-tools.readthedocs.io/en/latest/#using-hashes",
}
PROBE_COMMON = """
import importlib.metadata as metadata
import json, os, site, sys
paths = sorted({os.path.realpath(p) for p in site.getsitepackages() if os.path.isdir(p)})
result = {"executable": sys.executable, "prefix": os.path.realpath(sys.prefix),
          "base_prefix": os.path.realpath(sys.base_prefix), "site_packages": paths}
"""
TARGET_PROBE = PROBE_COMMON + """
result["inventory"] = sorted(
    [{"name": d.metadata["Name"], "version": d.version} for d in metadata.distributions()],
    key=lambda d: (str(d["name"]).lower(), d["version"]))
# Refuse packages injected outside the site directories the auditor will inspect.
result["outside_site_packages"] = sorted({os.path.realpath(d.locate_file(""))
    for d in metadata.distributions() if os.path.realpath(d.locate_file("")) not in paths})
import torch
result["torch"] = {"version": str(torch.__version__), "cuda": torch.version.cuda}
print(json.dumps(result))
"""
AUDITOR_PROBE = PROBE_COMMON + """
result["pip_audit_version"] = metadata.version("pip-audit")
result["pip_version"] = metadata.version("pip")
print(json.dumps(result))
"""


class AuditError(ValueError):
    """Incomplete, unexpected, or unsafe-to-interpret audit evidence."""


def canonical_name(name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
        raise AuditError(f"Invalid package name: {name!r}")
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_json(raw):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise AuditError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        result = json.loads(raw, object_pairs_hook=unique_keys)
    except (ValueError, TypeError) as exc:
        raise AuditError(f"Invalid or empty JSON report: {exc}") from exc
    if not isinstance(result, dict):
        raise AuditError("JSON report must be an object")
    return result


def inventory_map(inventory):
    if not isinstance(inventory, list) or not inventory:
        raise AuditError("Target inventory is missing or empty")
    result = {}
    for entry in inventory:
        if not isinstance(entry, dict) or set(entry) != {"name", "version"}:
            raise AuditError("Malformed target inventory entry")
        name = canonical_name(entry["name"])
        version = entry["version"]
        if not isinstance(version, str) or not version.strip():
            raise AuditError(f"Missing installed version for {name}")
        if name in result:
            raise AuditError(f"Duplicate installed package: {name}")
        result[name] = version
    return result


def isolated_environment():
    # pip-audit calls pip in a subprocess. Do not inherit an override that could
    # select another interpreter, a user package path, or a private package index.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("PIP_", "PIPAPI_", "PYTHON", "VIRTUAL_ENV"))}
    env.update(PIP_CONFIG_FILE=os.devnull, PIP_DISABLE_PIP_VERSION_CHECK="1",
               PIP_NO_INPUT="1", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1")
    return env


def run_command(command, cwd, env):
    record = {"command": command, "returncode": None, "stdout": "", "stderr": ""}
    try:
        completed = subprocess.run(command, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace",
                                   cwd=cwd, env=env, timeout=300, check=False)
        record.update(returncode=completed.returncode, stdout=completed.stdout,
                      stderr=completed.stderr)
    except (OSError, subprocess.TimeoutExpired) as exc:
        record["error"] = str(exc)
        # TimeoutExpired may contain bytes even with text=True. Retain evidence.
        for key in ("stdout", "stderr"):
            value = getattr(exc, key, None)
            if value:
                record[key] = value.decode(errors="replace") if isinstance(value, bytes) else value
    return record


def read_probe(record, label):
    if record["returncode"] != 0 or record["stderr"].strip():
        raise AuditError(f"{label} probe failed or emitted unexpected diagnostics")
    result = parse_json(record["stdout"])
    for key in ("executable", "prefix", "base_prefix"):
        if not isinstance(result.get(key), str) or not os.path.isabs(result[key]):
            raise AuditError(f"{label} probe has invalid {key}")
    paths = result.get("site_packages")
    if (not isinstance(paths, list) or not paths
            or any(not isinstance(p, str) or not os.path.isabs(p) for p in paths)
            or len(set(paths)) != len(paths)):
        raise AuditError(f"{label} probe has invalid site-packages paths")
    return result


def validate_report(record, expected, *, cpu_skip):
    """Require one-to-one name/version coverage; never trust exit status alone."""
    if record["returncode"] != 0:
        raise AuditError(f"Audit subprocess failed (exit {record['returncode']})")
    report = parse_json(record["stdout"])
    if set(report) != {"dependencies", "fixes"} or report["fixes"] != []:
        raise AuditError("Unexpected audit report fields or attempted fixes")
    entries = report["dependencies"]
    if not isinstance(entries, list) or not entries:
        raise AuditError("Audit dependencies are missing or empty")
    seen, skips, audited = set(), [], 0
    for entry in entries:
        if not isinstance(entry, dict):
            raise AuditError("Malformed audited dependency")
        name = canonical_name(entry.get("name"))
        if name in seen:
            raise AuditError(f"Duplicate audited package: {name}")
        seen.add(name)
        if name not in expected:
            raise AuditError(f"Unexpected audited package: {name}")
        if "skip_reason" in entry:
            if not (cpu_skip and name == "torch" and expected[name] == CPU_VERSION
                    and entry == {"name": "torch", "skip_reason": EXPECTED_SKIP}):
                raise AuditError(f"Unexpected package skip: {name}: {entry.get('skip_reason')}")
            skips.append(entry)
        else:
            if set(entry) != {"name", "version", "vulns"}:
                raise AuditError(f"Malformed audit coverage for {name}")
            if entry["version"] != expected[name]:
                raise AuditError(f"Audited version does not match installed/required {name}")
            if not isinstance(entry["vulns"], list) or entry["vulns"]:
                raise AuditError(f"Advisories or invalid vulnerability list for {name}")
            audited += 1
    if seen != set(expected):
        raise AuditError(f"Missing package coverage: {sorted(set(expected) - seen)}")
    if cpu_skip and len(skips) != 1:
        raise AuditError("Expected installed CPU-wheel skip was not preserved")
    allowed_diagnostics = {"No known vulnerabilities found"}
    if not cpu_skip:
        allowed_diagnostics |= BASE_WARNINGS
    diagnostics = {line.strip() for line in record["stderr"].splitlines() if line.strip()}
    if diagnostics - allowed_diagnostics:
        raise AuditError("Audit emitted unexpected diagnostics")
    return {"inventory_count": len(expected), "audited_count": audited, "skips": skips,
            "advisory_count": 0}


def audit(target_python, auditor_python):
    summary = {"schema_version": 1, "passed": False, "errors": [],
               "coverage_limitation": LIMITATION, "probes": {}, "audits": {}}
    # abspath preserves a venv's executable symlink; resolve() would lose the venv.
    target_python, auditor_python = map(os.path.abspath, (target_python, auditor_python))
    env = isolated_environment()
    try:
        with tempfile.TemporaryDirectory(prefix="bias-python-audit-") as work:
            # pip-audit invokes pip to inventory --path. Give that subprocess a
            # writable cache too, rather than suppressing cache/access warnings.
            pip_cache = Path(work) / "pip-cache"
            pip_cache.mkdir()
            env["PIP_CACHE_DIR"] = str(pip_cache)
            for label, python, code in (("target", target_python, TARGET_PROBE),
                                        ("auditor", auditor_python, AUDITOR_PROBE)):
                record = run_command([python, "-I", "-B", "-c", code], work, env)
                summary["probes"][label] = record
                summary[label] = read_probe(record, label)
            target, auditor = summary["target"], summary["auditor"]
            inventory = inventory_map(target.get("inventory"))
            if "pip" not in inventory:
                raise AuditError("Target inventory does not include pip")
            if (inventory.get("torch") != CPU_VERSION
                    or target.get("torch") != {"version": CPU_VERSION, "cuda": None}):
                raise AuditError(f"Target must contain the exact CPU torch=={CPU_VERSION}, CUDA=None")
            if target.get("outside_site_packages") != []:
                raise AuditError("Target contains packages outside audited site-packages")
            if (auditor["prefix"] == target["prefix"]
                    or auditor["prefix"] == auditor["base_prefix"]
                    or set(auditor["site_packages"]) & set(target["site_packages"])
                    or any(not Path(p).is_relative_to(auditor["prefix"])
                           for p in auditor["site_packages"])):
                raise AuditError("Auditor must be a separate isolated virtualenv")
            if auditor.get("pip_audit_version") != AUDITOR_VERSION:
                raise AuditError(f"Expected pip-audit=={AUDITOR_VERSION}")
            base = [auditor_python, "-I", "-B", "-m", "pip_audit", "--format", "json",
                    "--aliases", "on", "--progress-spinner", "off",
                    "--vulnerability-service", "pypi", "--timeout", "30",
                    "--cache-dir", str(Path(work) / "cache")]
            installed = base + [arg for p in target["site_packages"] for arg in ("--path", p)]
            requirement = Path(work) / "torch-base-version.txt"
            requirement.write_text(f"torch=={BASE_VERSION}\n", encoding="utf-8")
            normalized = base + ["-r", str(requirement), "--no-deps", "--disable-pip"]
            # --strict stops before producing the expected torch skip. Instead,
            # inspect every entry, including every skip, in the complete reports.
            for label, command, expected, cpu_skip in (
                ("installed", installed, inventory, True),
                ("torch_base_version", normalized, {"torch": BASE_VERSION}, False),
            ):
                record = run_command(command, work, env)
                summary["audits"][label] = record
                try:
                    record["coverage"] = validate_report(record, expected, cpu_skip=cpu_skip)
                except AuditError as exc:
                    summary["errors"].append(f"{label}: {exc}")
    except (AuditError, OSError) as exc:
        summary["errors"].append(str(exc))
    summary["passed"] = not summary["errors"] and len(summary["audits"]) == 2
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-python", required=True)
    parser.add_argument("--auditor-python", required=True)
    args = parser.parse_args(argv)
    summary = audit(args.target_python, args.auditor_python)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
