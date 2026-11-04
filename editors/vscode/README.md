# Hypomnesis pour VS Code

Coloration des fichiers `.hyp`, commentaires imbriqués et descriptions `(** … *)`,
délimiteurs, repliement par indentation et régions `(* #region … *)`.
Les diagnostics de syntaxe, de résolution des noms et de types proviennent du compilateur,
sans exécuter les programmes ni importer les adaptateurs du langage.

## Construire et installer

Depuis la racine du dépôt :

Construction : Node.js 22 ou supérieur et Python 3.11 ou supérieur.

```bash
uv pip install --python .venv/bin/python -e '.[lsp]'
cd editors/vscode
npm ci
npm test
npm run package
code --install-extension hypomnesis.vsix
```

Sans commande `code`, utiliser **Extensions → … → Installer à partir d'un VSIX…** et
sélectionner `editors/vscode/hypomnesis.vsix`. Recharger la fenêtre si VS Code le demande.
La coloration ne requiert pas Python ; les diagnostics exigent un dossier approuvé.

Test d'intégration facultatif dans une instance VS Code isolée (sans installation utilisateur) :

```bash
VSCODE_EXECUTABLE="/Applications/Visual Studio Code.app/Contents/MacOS/Code" npm run test:host
```

`VSCODE_EXECUTABLE` doit pointer sur l'exécutable de l'application, pas sur un lanceur qui
rend la main avant la fin des tests. `HYPOMNESIS_PYTHON` permet de remplacer le Python du
dépôt utilisé pour ce test. Un fichier témoin confirme que les assertions ont bien été exécutées.

## Réglages

- `hypomnesis.pythonPath` : Python avec l'extra `lsp` ; par défaut le `.venv` du dossier
  ouvert, sinon `python3` (`python` sous Windows). Un chemin relatif est résolu depuis ce
  dossier. Ne pas ajouter d'arguments au chemin.
- `hypomnesis.languageRoot` : dossier contenant `langage.json`, relatif au dossier ouvert
  ou absolu. Vide : manifeste dans le dossier du fichier ou ses parents ; pour
  `programs/<nom>/…`, recherche aussi `languages/<nom>/langage.json`.
- `hypomnesis.debounceMs` : délai de frappe, 300 ms par défaut (0 à 5 000 ms).

Un serveur est lancé par dossier dans un espace de travail multi-racines. Un changement
de réglage relance les serveurs. Le serveur lit les textes non enregistrés, y compris les
sources M2 ouvertes, vérifie les sources du manifeste dans l'ordre et annule les analyses
obsolètes. Les diagnostics disparaissent après correction et à la fermeture du fichier.
Le compilateur signale la première erreur ; les erreurs d'une dépendance ou du manifeste
sont indiquées au début du document avec le chemin concerné. Survol, complétion et
navigation ne sont pas inclus.

Pour `programs/mecanique/plaque_120x80.hyp`, la détection est automatique en ouvrant la
racine du dépôt. Dans un autre dossier, régler par exemple :

```json
{
  "hypomnesis.pythonPath": "/chemin/Hypomnesis/.venv/bin/python",
  "hypomnesis.languageRoot": "/chemin/Hypomnesis/languages/mecanique"
}
```

Les erreurs de démarrage sont affichées ; les détails du serveur sont dans
**Affichage → Sortie → Hypomnesis**. Le serveur est utilisable par tout client LSP :
`hypomnesis-lsp` ou `python -m hypomnesis.lsp.server`, transport stdio, positions UTF-16
par défaut (UTF-8 et UTF-32 également négociables). La dépendance transitive `minimatch`
est forcée à une version corrigée par `overrides` dans le manifeste npm.
