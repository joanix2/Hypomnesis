const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vscode = require("vscode");
const { loadTokenizer, scoped } = require("./tokenize.cjs");

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
  const declaration = await vscode.workspace.openTextDocument(
    vscode.Uri.joinPath(folder.uri, "langage.hyp"),
  );
  await vscode.window.showTextDocument(declaration);
  assert.equal(declaration.languageId, "hypomnesis");
  const extension = vscode.extensions.getExtension("hypomnesis.hypomnesis");
  assert(extension?.isActive, "Hypomnesis extension must actually be active");
  const contributed = extension.packageJSON.contributes.grammars.find(g => g.language === "hypomnesis");
  const tokenize = await loadTokenizer(path.join(extension.extensionPath, contributed.path));
  const tokens = tokenize(declaration.getText());
  for (const [scope, text] of [
    ["keyword.control.hypomnesis", "language"],
    ["entity.name.type.language.hypomnesis", "arithmetique"],
    ["variable.other.property.hypomnesis", "version"],
    ["variable.other.property.hypomnesis", "description"],
    ["string.quoted.double.hypomnesis", "1.0.0"],
    ["keyword.operator.hypomnesis", "="],
    ["punctuation.section.hypomnesis", "{"],
  ]) assert(scoped(tokens, scope, text), `${scope}: ${text}`);
  console.log("Hypomnesis Extension Host: association, activation, grammar scopes, diagnostic and correction OK");
  fs.writeFileSync(process.env.HYPOMNESIS_TEST_RESULT, "passed");
};
