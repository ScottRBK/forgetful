"""Prove the configured import rules using isolated packages and the real checker."""

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import grimp
import pytest

ROOT = Path(__file__).resolve().parents[2]
CASES = [
    ("foundation", "app.models.write_plugin_models", "app.config.write_plugin"),
    ("foundation", "app.protocols.write_plugin_protocol", "app.config.write_plugin"),
    ("services", "app.services.write_plugin_service", "app.config.write_plugin"),
    ("routes", "app.routes.mcp.handler", "app.config.write_plugin"),
    ("routes", "app.routes.api.handler", "app.config.write_plugin"),
    ("cli", "app.routes.cli.handler", "app.config.write_plugin"),
    ("foundation", "app.models.memory_models", "app.services.memory_service"),
    ("services", "app.services.re_embedding_service", "app.repositories.provider"),
    ("repositories", "app.repositories.provider", "app.services.memory_service"),
    ("external", "app.services.re_embedding_service", "subprocess"),
    ("routes", "app.routes.mcp.handler", "app.repositories.provider"),
    ("cli", "app.routes.cli.handler", "app.repositories.provider"),
    ("cli", "app.routes.cli.handler", "app.bootstrap"),
]


def configuration():
    return tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["importlinter"]


def write_module(root, name, code=""):
    """Use packages throughout so Grimp sees every fixture module."""
    directory = root
    for part in name.split("."):
        directory /= part
        directory.mkdir(exist_ok=True)
        (directory / "__init__.py").touch()
    (directory / "__init__.py").write_text(code)


def write_config(root, options, contracts):
    lines = ["[tool.importlinter]"]
    lines += [f"{key} = {json.dumps(value)}" for key, value in options.items()
              if key != "contracts"]
    for contract in contracts:
        lines.append("[[tool.importlinter.contracts]]")
        lines += [f"{key} = {json.dumps(value)}" for key, value in contract.items()]
    (root / "pyproject.toml").write_text("\n".join(lines))


def write_startup(root):
    """Keep the permitted startup imports present, including both CLI exceptions."""
    write_module(root, "app.bootstrap", (
        "import app.repositories\nimport app.services\nimport app.config.write_plugin\n"
    ))
    write_module(root, "app.routes.cli.local_executor", "import app.bootstrap\n")
    write_module(root, "app.routes.cli.context", "import app.bootstrap\n")
    write_module(root, "app.routes.cli.command", "import app.routes.cli.local_executor\n")


def check(root):
    result = subprocess.run(
        [sys.executable, "-c",
         "from importlinter.cli import lint_imports_command; lint_imports_command()",
         "--config", "pyproject.toml", "--no-cache", "--no-logo"],
        cwd=root, env={**os.environ, "PYTHONPATH": str(root), "NO_COLOR": "1"},
        text=True, capture_output=True, timeout=15,
    )
    return result.returncode, result.stdout + result.stderr


@pytest.mark.parametrize("contract_id,source,target", CASES, ids=[case[0] for case in CASES])
@pytest.mark.parametrize("style", ["direct", "indirect", "type_checking", "reexport", "local"])
def test_contract_rejects_forbidden_dependency(tmp_path, contract_id, source, target, style):
    options = configuration()
    contract = next(c for c in options["contracts"] if c["id"] == contract_id)
    for configured in options["contracts"]:
        for module in configured["source_modules"] + configured["forbidden_modules"]:
            if module.startswith("app."):
                write_module(tmp_path, module)
    if target.startswith("app."):
        write_module(tmp_path, target)
    # This intermediary sits outside both endpoints and every restricted source area.
    bridge = "app.boundary_probe.bridge"
    write_module(tmp_path, bridge, f"import {target} as exported\n")
    write_module(tmp_path, source)
    # Legitimate startup wiring and service-to-protocol imports must remain allowed.
    write_startup(tmp_path)
    write_module(tmp_path, "app.services.allowed", "import app.protocols\n")

    write_config(tmp_path, options, [contract])
    status, output = check(tmp_path)
    assert status == 0, output

    imports = {
        "direct": f"import {target}\n",
        "indirect": f"import {bridge}\n",
        "type_checking": (
            f"from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import {target}\n"
        ),
        "reexport": f"from {bridge} import exported\n",
        "local": f"def load():\n    import {target}\n",
    }
    write_module(tmp_path, source, imports[style])
    # Isolate each contract because several production rules intentionally overlap.
    write_config(tmp_path, options, [])
    status, output = check(tmp_path)
    assert status == 0, output

    write_config(tmp_path, options, [contract])
    status, output = check(tmp_path)
    assert status == 1, output
    assert f'{contract["name"]} BROKEN' in output, output
    assert source in output and target in output, output
    if style in ("indirect", "reexport"):
        assert bridge in output, output

    write_module(tmp_path, source)
    status, output = check(tmp_path)
    assert status == 0, output


@pytest.mark.parametrize("startup_module", ["local_executor", "context"])
def test_http_cannot_reach_bootstrap_through_cli(tmp_path, startup_module):
    options = configuration()
    for configured in options["contracts"]:
        for module in configured["source_modules"] + configured["forbidden_modules"]:
            if module.startswith("app."):
                write_module(tmp_path, module)
    write_startup(tmp_path)
    write_module(tmp_path, "app.routes.mcp.handler")
    write_config(tmp_path, options, options["contracts"])
    status, output = check(tmp_path)
    assert status == 0, output

    startup = f"app.routes.cli.{startup_module}"
    write_module(tmp_path, "app.routes.mcp.handler", f"import {startup}\n")
    status, output = check(tmp_path)
    assert status == 1, output
    assert "HTTP and MCP handlers use services instead of repositories or bootstrap BROKEN" in output
    assert "app.routes.mcp.handler" in output
    assert startup in output
    assert "app.bootstrap" in output


def test_every_app_file_is_visible_to_checker():
    graph = grimp.build_graph("app", cache_dir=None)
    expected = set()
    for path in (ROOT / "app").rglob("*.py"):
        parts = list(path.relative_to(ROOT).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        expected.add(".".join(parts))
    assert expected <= graph.modules, f"Unscanned modules: {sorted(expected - graph.modules)}"
    internal_targets = {
        name for contract in configuration()["contracts"]
        for name in contract["forbidden_modules"] if name.startswith("app.")
    }
    assert internal_targets <= graph.modules, (
        f"Unknown forbidden modules: {sorted(internal_targets - graph.modules)}"
    )


def test_repository_obeys_contracts():
    status, output = check(ROOT)
    assert status == 0, output
