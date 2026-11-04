const assert = require("node:assert/strict");
const fs = require("node:fs");
const vscode = require("vscode");

async function waitFor(predicate) {
  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) {
    if (predicate()) return;
    await new Promise(resolve => setTimeout(resolve, 50));
  }
  throw new Error("Timed out waiting for VS Code diagnostics");
}

exports.run = async () => {
  const folder = vscode.workspace.workspaceFolders[0];
  const uri = vscode.Uri.joinPath(folder.uri, "probe.hyp");
  const document = await vscode.workspace.openTextDocument(uri);
  await vscode.window.showTextDocument(document);
  assert.equal(document.languageId, "hypomnesis");
  await waitFor(() => vscode.languages.getDiagnostics(uri).some(d => d.source === "hypomnesis"));
  const [issue] = vscode.languages.getDiagnostics(uri).filter(d => d.source === "hypomnesis");
  assert.equal(issue.range.start.line, 0);
  assert.equal(issue.range.start.character, 8);
  assert.match(issue.message, /has type bool/);
  const edit = new vscode.WorkspaceEdit();
  edit.replace(uri, new vscode.Range(0, 0, document.lineCount, 0), "let x = 1 + 1\n");
  assert(await vscode.workspace.applyEdit(edit));
  await waitFor(() => vscode.languages.getDiagnostics(uri).length === 0);
  console.log("Hypomnesis Extension Host: language association, compiler diagnostic and unsaved correction OK");
  fs.writeFileSync(process.env.HYPOMNESIS_TEST_RESULT, "passed");
};
