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
    ["keyword.control.hypomnesis", "struct"],
    ["keyword.control.hypomnesis", "let"],
    ["keyword.control.hypomnesis", "end"],
  ]) assert(scoped(tokens, scope, text), `${scope}: ${text}`);
  const original = declaration.getText();
  const legacy = new vscode.WorkspaceEdit();
  legacy.replace(
    declaration.uri, new vscode.Range(0, 0, declaration.lineCount, 0),
    'language arithmetique = { version = "1.0.0" }\n',
  );
  assert(await vscode.workspace.applyEdit(legacy));
  await waitFor(() => vscode.languages.getDiagnostics(declaration.uri).some(
    diagnostic => diagnostic.source === "hypomnesis" && diagnostic.code === "syntax",
  ));
  const restore = new vscode.WorkspaceEdit();
  restore.replace(declaration.uri, new vscode.Range(0, 0, declaration.lineCount, 0), original);
  assert(await vscode.workspace.applyEdit(restore));
  await waitFor(() => vscode.languages.getDiagnostics(declaration.uri).length === 0);
  const imports = new vscode.WorkspaceEdit();
  imports.replace(uri, new vscode.Range(0, 0, document.lineCount, 0),
    "import units\nlet answer = units.mm 41 + 1\n");
  assert(await vscode.workspace.applyEdit(imports));
  const dependency = await vscode.workspace.openTextDocument(
    vscode.Uri.joinPath(folder.uri, "units.hyp"),
  );
  const changeDependency = new vscode.WorkspaceEdit();
  changeDependency.replace(dependency.uri, new vscode.Range(0, 0, dependency.lineCount, 0),
    "(** Boolean. *)\nlet mm x = true\n");
  assert(await vscode.workspace.applyEdit(changeDependency));
  await waitFor(() => vscode.languages.getDiagnostics(uri).some(
    diagnostic => diagnostic.source === "hypomnesis" && diagnostic.code === "type",
  ));
  const useImported = new vscode.WorkspaceEdit();
  useImported.replace(uri, new vscode.Range(0, 0, document.lineCount, 0),
    "import units\nlet answer = units.mm 41 && true\n");
  assert(await vscode.workspace.applyEdit(useImported));
  await waitFor(() => vscode.languages.getDiagnostics(uri).length === 0);
  console.log("Hypomnesis Extension Host: association, activation, scopes, legacy rejection, imports and unsaved dependency OK");
  fs.writeFileSync(process.env.HYPOMNESIS_TEST_RESULT, "passed");
};
