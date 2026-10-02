"""Synthetic audit subprocess fixtures. No package installs or network queries."""
import copy
import json
from pathlib import Path
import subprocess

import pytest

from research.scripts import audit_python_dependencies as module


@pytest.fixture
def evidence():
    target = {"executable": "/target/bin/python", "prefix": "/target",
              "base_prefix": "/system", "site_packages": ["/target/lib/site-packages"],
              "inventory": [{"name": "pip", "version": "26.2"},
                            {"name": "Some_Package", "version": "1.0"},
                            {"name": "torch", "version": module.CPU_VERSION}],
              "outside_site_packages": [],
              "torch": {"version": module.CPU_VERSION, "cuda": None}}
    auditor = {"executable": "/auditor/bin/python", "prefix": "/auditor",
               "base_prefix": "/system", "site_packages": ["/auditor/lib/site-packages"],
               "pip_audit_version": module.AUDITOR_VERSION, "pip_version": "26.2"}
    installed = {"dependencies": [
        {"name": "pip", "version": "26.2", "vulns": []},
        {"name": "some-package", "version": "1.0", "vulns": []},
        {"name": "torch", "skip_reason": module.EXPECTED_SKIP}], "fixes": []}
    normalized = {"dependencies": [{"name": "torch", "version": module.BASE_VERSION,
                                    "vulns": []}], "fixes": []}
    return {"target": target, "auditor": auditor, "installed": installed,
            "torch_base_version": normalized}


def mock_commands(monkeypatch, evidence, overrides=None):
    calls = []
    overrides = overrides or {}

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        cache = Path(kwargs["env"]["PIP_CACHE_DIR"])
        assert cache.is_dir() and cache.parent == Path(kwargs["cwd"])
        if "-c" in command:
            label = "target" if command[-1] == module.TARGET_PROBE else "auditor"
        else:
            label = "installed" if "--path" in command else "torch_base_version"
            assert command[command.index("--vulnerability-service") + 1] == "pypi"
            assert "--ignore-vuln" not in command
            assert "--fix" not in command
            if label == "torch_base_version":
                assert "--no-deps" in command and "--disable-pip" in command
                assert Path(command[command.index("-r") + 1]).read_text() == "torch==2.13.0\n"
        if isinstance(overrides.get(label), Exception):
            raise overrides[label]
        values = {"returncode": 0, "stdout": json.dumps(evidence[label]),
                  "stderr": "" if "-c" in command else "No known vulnerabilities found\n"}
        values.update(overrides.get(label, {}))
        return subprocess.CompletedProcess(command, **values)

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    return calls


def run_gate(monkeypatch, evidence, overrides=None):
    mock_commands(monkeypatch, evidence, overrides)
    return module.audit("/target/bin/python", "/auditor/bin/python")


def test_success_preserves_inventory_skip_raw_reports_and_isolation(monkeypatch, evidence):
    monkeypatch.setenv("PIPAPI_PYTHON_LOCATION", "/unrelated/python")
    monkeypatch.setenv("PYTHONPATH", "/unrelated/packages")
    monkeypatch.setenv("PIP_INDEX_URL", "https://unrelated.invalid")
    calls = mock_commands(monkeypatch, evidence)
    result = module.audit("/target/bin/python", "/auditor/bin/python")
    assert result["passed"] and result["errors"] == []
    assert result["target"]["inventory"] == evidence["target"]["inventory"]
    assert result["audits"]["installed"]["coverage"] == {
        "inventory_count": 3, "audited_count": 2, "advisory_count": 0,
        "skips": [{"name": "torch", "skip_reason": module.EXPECTED_SKIP}]}
    assert "binary-specific" in result["coverage_limitation"]
    for label in ("installed", "torch_base_version"):
        assert json.loads(result["audits"][label]["stdout"]) == evidence[label]
    assert len(calls) == 4
    for command, kwargs in calls:
        assert command[1] == "-I"
        assert "-B" in command and kwargs["env"]["PYTHONDONTWRITEBYTECODE"] == "1"
        assert kwargs["timeout"] == 300
        assert not {"PYTHONPATH", "PIPAPI_PYTHON_LOCATION", "PIP_INDEX_URL"} & kwargs["env"].keys()
    assert calls[2][0][-2:] == ["--path", "/target/lib/site-packages"]


@pytest.mark.parametrize("label", ["installed", "torch_base_version"])
def test_advisory_fails_even_if_tool_exits_zero(monkeypatch, evidence, label):
    evidence[label]["dependencies"][0]["vulns"] = [{"id": "TEST-ADVISORY", "aliases": []}]
    result = run_gate(monkeypatch, evidence)
    assert not result["passed"]
    assert any("Advisories" in error for error in result["errors"])
    assert len(result["audits"]) == 2


@pytest.mark.parametrize("label,index", [("installed", 0), ("torch_base_version", 0)])
def test_unexpected_skip_fails(monkeypatch, evidence, label, index):
    name = evidence[label]["dependencies"][index]["name"]
    evidence[label]["dependencies"][index] = {"name": name, "skip_reason": "Network failure"}
    result = run_gate(monkeypatch, evidence)
    assert not result["passed"]
    assert any("Unexpected package skip" in error for error in result["errors"])


@pytest.mark.parametrize("change", ["metadata_version", "runtime_version", "cuda", "missing_cuda"])
def test_wrong_cpu_runtime_fails_before_audits(monkeypatch, evidence, change):
    if change == "metadata_version":
        evidence["target"]["inventory"][-1]["version"] = module.BASE_VERSION
    elif change == "runtime_version":
        evidence["target"]["torch"]["version"] = "2.6.0+cpu"
    elif change == "cuda":
        evidence["target"]["torch"]["cuda"] = "12.8"
    else:
        del evidence["target"]["torch"]["cuda"]
    result = run_gate(monkeypatch, evidence)
    assert not result["passed"] and result["audits"] == {}
    assert "exact CPU torch" in result["errors"][0]


@pytest.mark.parametrize("label", ["installed", "torch_base_version"])
@pytest.mark.parametrize("raw", ["", "not-json", "[]", "{}", '{"dependencies":[],"fixes":[]}',
                                 '{"dependencies":[],"dependencies":[],"fixes":[]}'])
def test_empty_malformed_or_duplicate_key_reports_fail(monkeypatch, evidence, label, raw):
    result = run_gate(monkeypatch, evidence, {label: {"stdout": raw}})
    assert not result["passed"] and result["errors"]


@pytest.mark.parametrize("label", ["target", "auditor", "installed", "torch_base_version"])
@pytest.mark.parametrize("failure", ["exit", "timeout", "missing_executable"])
def test_subprocess_failures_are_json_evidence(monkeypatch, evidence, label, failure):
    override = {"returncode": 1, "stderr": "failed"}
    if failure == "timeout":
        override = subprocess.TimeoutExpired(["python"], 300, output=b"partial output")
    elif failure == "missing_executable":
        override = FileNotFoundError("No interpreter")
    result = run_gate(monkeypatch, evidence, {label: override})
    assert not result["passed"] and result["errors"]
    json.dumps(result)


def test_missing_pip_coverage_fails(monkeypatch, evidence):
    del evidence["installed"]["dependencies"][0]
    result = run_gate(monkeypatch, evidence)
    assert not result["passed"]
    assert "Missing package coverage: ['pip']" in result["errors"][0]


@pytest.mark.parametrize("change", ["missing_pip", "empty_inventory", "duplicate_inventory",
                                    "outside_path", "same_auditor", "shared_site", "global_auditor",
                                    "auditor_system_site", "wrong_auditor_version"])
def test_invalid_inventory_or_auditor_fails(monkeypatch, evidence, change):
    target, auditor = evidence["target"], evidence["auditor"]
    if change == "missing_pip":
        del target["inventory"][0]
    elif change == "empty_inventory":
        target["inventory"] = []
    elif change == "duplicate_inventory":
        target["inventory"].append(copy.deepcopy(target["inventory"][0]))
    elif change == "outside_path":
        target["outside_site_packages"] = ["/unexpected"]
    elif change == "same_auditor":
        auditor["prefix"] = target["prefix"]
    elif change == "shared_site":
        auditor["site_packages"] += target["site_packages"]
    elif change == "global_auditor":
        auditor["prefix"] = auditor["base_prefix"]
    elif change == "auditor_system_site":
        auditor["site_packages"].append("/system/lib/site-packages")
    else:
        auditor["pip_audit_version"] = "0.0.0"
    result = run_gate(monkeypatch, evidence)
    assert not result["passed"] and result["audits"] == {}


@pytest.mark.parametrize("change", ["duplicate_package", "extra_package", "version", "skip_reason",
                                    "missing_skip", "vulns_null", "error_field", "fixes"])
def test_misleading_coverage_fails(monkeypatch, evidence, change):
    report = evidence["installed"]
    if change == "duplicate_package":
        report["dependencies"].append(copy.deepcopy(report["dependencies"][0]))
    elif change == "extra_package":
        report["dependencies"].append({"name": "unexpected", "version": "1", "vulns": []})
    elif change == "version":
        report["dependencies"][0]["version"] = "25.0.1"
    elif change == "skip_reason":
        report["dependencies"][-1]["skip_reason"] += "; network failure"
    elif change == "missing_skip":
        report["dependencies"][-1] = {"name": "torch", "version": module.CPU_VERSION, "vulns": []}
    elif change == "vulns_null":
        report["dependencies"][0]["vulns"] = None
    elif change == "error_field":
        report["errors"] = ["partial result"]
    else:
        report["fixes"] = [{"name": "pip"}]
    assert not run_gate(monkeypatch, evidence)["passed"]


@pytest.mark.parametrize("label", ["target", "auditor", "installed", "torch_base_version"])
def test_unexpected_diagnostics_fail(monkeypatch, evidence, label):
    assert not run_gate(monkeypatch, evidence, {label: {"stderr": "WARNING: partial audit"}})["passed"]


def test_known_no_deps_warnings_are_preserved(monkeypatch, evidence):
    stderr = "\n".join(sorted(module.BASE_WARNINGS)) + "\nNo known vulnerabilities found\n"
    result = run_gate(monkeypatch, evidence, {"torch_base_version": {"stderr": stderr}})
    assert result["passed"]
    assert result["audits"]["torch_base_version"]["stderr"] == stderr


@pytest.mark.parametrize("success", [True, False])
def test_cli_outputs_one_json_record_and_failure_exit(monkeypatch, evidence, capsys, success):
    if not success:
        evidence["installed"]["dependencies"] = []
    mock_commands(monkeypatch, evidence)
    exit_code = module.main(["--target-python", "/target/bin/python",
                             "--auditor-python", "/auditor/bin/python"])
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out)["passed"] is success
    assert exit_code == (0 if success else 1)
