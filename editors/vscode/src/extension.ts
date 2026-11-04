import * as fs from "node:fs";
import * as path from "node:path";
import * as vscode from "vscode";
import {
  LanguageClient,
  LanguageClientOptions,
  ServerOptions,
} from "vscode-languageclient/node";

const clients = new Map<string, LanguageClient>();

async function start(folder: vscode.WorkspaceFolder, output: vscode.LogOutputChannel): Promise<void> {
  if (!vscode.workspace.isTrusted || clients.has(folder.uri.toString())) {
    return;
  }
  const config = vscode.workspace.getConfiguration("hypomnesis", folder.uri);
  const configured = config.get<string>("pythonPath", "");
  const local = path.join(
    folder.uri.fsPath, ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python",
  );
  const command = configured
    ? (path.isAbsolute(configured) || !/[\\/]/.test(configured)
      ? configured : path.resolve(folder.uri.fsPath, configured))
    : (fs.existsSync(local) ? local : (process.platform === "win32" ? "python" : "python3"));
  const serverOptions: ServerOptions = {
    command,
    args: ["-m", "hypomnesis.lsp.server"],
    options: { cwd: folder.uri.fsPath },
  };
  const clientOptions: LanguageClientOptions = {
    documentSelector: [{
      scheme: "file",
      language: "hypomnesis",
      pattern: folder.uri.fsPath.replace(/\\/g, "/").replace(/[?*[\]{}()!+@]/g, "\\$&") + "/**/*.hyp",
    }],
    workspaceFolder: folder,
    initializationOptions: {
      languageRoot: config.get<string>("languageRoot", ""),
      debounceMs: config.get<number>("debounceMs", 300),
    },
    outputChannel: output,
  };
  const client = new LanguageClient(
    "hypomnesis", `Hypomnesis (${folder.name})`, serverOptions, clientOptions,
  );
  clients.set(folder.uri.toString(), client);
  try {
    await client.start();
  } catch (error) {
    clients.delete(folder.uri.toString());
    output.error(String(error));
    void vscode.window.showErrorMessage(
      "Hypomnesis : serveur indisponible. Installez hypomnesis[lsp] dans le Python " +
      "choisi par hypomnesis.pythonPath. Voir Sortie > Hypomnesis.",
    );
    await client.dispose();
  }
}

export async function activate(context: vscode.ExtensionContext): Promise<void> {
  const output = vscode.window.createOutputChannel("Hypomnesis", { log: true });
  context.subscriptions.push(output);
  const startAll = async (): Promise<void> => {
    await Promise.all((vscode.workspace.workspaceFolders ?? []).map(folder => start(folder, output)));
  };
  context.subscriptions.push(
    vscode.workspace.onDidGrantWorkspaceTrust(() => { void startAll(); }),
    vscode.workspace.onDidChangeWorkspaceFolders(async event => {
      for (const folder of event.removed) {
        const client = clients.get(folder.uri.toString());
        clients.delete(folder.uri.toString());
        await client?.dispose();
      }
      await startAll();
    }),
    vscode.workspace.onDidChangeConfiguration(async event => {
      if (event.affectsConfiguration("hypomnesis")) {
        await deactivate();
        await startAll();
      }
    }),
  );
  await startAll();
}

export async function deactivate(): Promise<void> {
  const running = [...clients.values()];
  clients.clear();
  await Promise.all(running.map(client => client.dispose()));
}
