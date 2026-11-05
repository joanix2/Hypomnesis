const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const code = process.env.VSCODE_EXECUTABLE;
if (!code) {
  console.error("Set VSCODE_EXECUTABLE to the VS Code CLI executable.");
  process.exitCode = 1;
} else {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), "hypomnesis-vscode-"));
  try {
    const workspace = path.join(temp, "workspace");
    fs.mkdirSync(path.join(workspace, ".vscode"), { recursive: true });
    const python = process.env.HYPOMNESIS_PYTHON
      || path.resolve(__dirname, "../../../.venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
    fs.writeFileSync(path.join(workspace, ".vscode/settings.json"), JSON.stringify({
      "hypomnesis.pythonPath": python,
      "hypomnesis.debounceMs": 20,
    }));
    fs.writeFileSync(path.join(workspace, "probe.hyp"), "let x = true + 1\n");
    fs.copyFileSync(path.join(__dirname, "fixtures/language.hyp"), path.join(workspace, "langage.hyp"));
    const report = path.join(temp, "result.txt");
    const result = spawnSync(code, [
      workspace, "--new-window", "--skip-welcome", "--skip-release-notes",
      "--disable-workspace-trust", "--disable-updates",
      `--user-data-dir=${path.join(temp, "user")}`,
      `--extensions-dir=${path.join(temp, "extensions")}`,
      `--extensionDevelopmentPath=${path.resolve(__dirname, "..")}`,
      `--extensionTestsPath=${path.join(__dirname, "extension-host.cjs")}`,
    ], {
      stdio: "inherit", timeout: 90000,
      env: { ...process.env, HYPOMNESIS_TEST_RESULT: report },
    });
    if (result.error) console.error(result.error.message);
    const passed = fs.existsSync(report) && fs.readFileSync(report, "utf8") === "passed";
    if (!passed) console.error("Extension Host did not confirm the end-to-end assertions.");
    process.exitCode = passed ? (result.status ?? 1) : 1;
  } finally {
    fs.rmSync(temp, { recursive: true, force: true });
  }
}
