"""A local agent workflow using only versioned CLI JSON, with no model involved."""

import json
import subprocess
import sys
import textwrap
from pathlib import Path

from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.language.errors import DIAGNOSTICS_SCHEMA_ID

ROOT = Path(__file__).resolve().parents[2]
LANGUAGE = ROOT / "demo/languages/ventilation"
CATALOGUE_ID = "https://schemas.example.org/hypomnesis/language-catalogue/1.0.0"
EXECUTION_ID = "https://schemas.example.org/hypomnesis/cli-execution/1.0.0"


def invoke(module, *arguments):
    return subprocess.run(
        [sys.executable, "-m", module, *map(str, arguments)],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )


def document(process, schema_id, status):
    assert process.returncode == status, process.stdout + process.stderr
    result = json.loads(process.stdout)
    SchemaRegistry.with_builtin_schemas().validate(schema_id, result)
    assert result["version"] == "1.0.0"
    return result


def test_discover_write_repair_check_and_simulate_using_only_json(tmp_path):
    described = document(
        invoke("hypomnesis_codegen.cli", "decrire", LANGUAGE, "--format", "json"),
        CATALOGUE_ID,
        0,
    )
    module = next(m for m in described["modules"] if m["path"] == "Ventilation")
    assert described["entry"] == "procedure"
    assert any(v["path"] == "Ventilation.reguler" for v in module["values"])
    installation = next(t for t in module["types"] if t["path"].endswith(".installation"))
    assert next(f["type"] for f in installation["fields"] if f["path"].endswith(".budget")) == "int"
    skeleton = textwrap.dedent(next(value for tag, value in module["tags"] if tag == "squelette"))
    assert "budget = 3" in skeleton
    program = tmp_path / "agent.hyp"
    program.write_text(skeleton.replace("budget = 3", "budget = true"), encoding="utf-8")
    checked = document(
        invoke("hypomnesis", "check", program, "--langage", LANGUAGE, "--format", "json"),
        DIAGNOSTICS_SCHEMA_ID,
        1,
    )
    error = next(d for d in checked["diagnostics"] if d["severity"] == "error")
    assert error["stage"] == "type"
    assert "int" in error["message"] and "bool" in error["message"]
    assert error["file"] == str(program) and error["line"] > 0 and error["column"] > 0
    program.write_text(skeleton, encoding="utf-8")
    checked = document(
        invoke("hypomnesis", "check", program, "--langage", LANGUAGE, "--format", "json"),
        DIAGNOSTICS_SCHEMA_ID,
        0,
    )
    assert not [d for d in checked["diagnostics"] if d["severity"] == "error"]
    for mode, terminal in (("simulate", "Simulated"), ("dry-run", "DryRun")):
        result = document(
            invoke(
                "hypomnesis",
                "lancer",
                LANGUAGE,
                program,
                "--mode",
                mode,
                "--format",
                "json",
                "--sortie",
                tmp_path / mode,
                "--generated",
            ),
            EXECUTION_ID,
            0,
        )
        assert result["status"] == "ok" and result["mode"] == mode
        report = result["report"]
        assert report["generated"] is True and report["steps"] > 0
        assert report["commands"] and report["journal"]
        assert all(command["states"][-1][0] == terminal for command in report["commands"])
        assert (tmp_path / mode / "rapport.json").is_file()
        assert not any(span["name"] == "actuator.execute" for span in report["trace"]["spans"])
