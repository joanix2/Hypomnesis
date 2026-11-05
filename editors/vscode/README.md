# Hypomnesis pour VS Code

Coloration des fichiers `.hyp`, commentaires imbriqués et descriptions `(** … *)`,
délimiteurs, repliement par indentation et régions `(* #region … *)`.
Les diagnostics de syntaxe, de résolution des noms et de types proviennent du compilateur,
sans exécuter les programmes ni importer les adaptateurs du langage.

La version 0.1.3 colore aussi les imports `import units`, `from units import mm`
et `as`. Les diagnostics suivent les dépendances `.hyp` transitives et leurs
modifications non enregistrées ; `open` ne charge jamais de fichier.

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

## Déclarations `language` et diagnostic de coloration

Depuis 0.1.2, la déclaration utilise `struct / let / end` ; l'ancienne forme
extérieure à accolades est rejetée par le compilateur. Le nom et les clés ont des scopes
dédiés, en plus du mot-clé, des chaînes, opérateurs et délimiteurs :

```hyp
language arithmetique = struct
  let version = "1.0.0"
  let description = "Arithmétique entière réutilisable, sans entrée/sortie."
end
```

Le nom reçoit `entity.name.type.language.hypomnesis`, les clés
`variable.other.property.hypomnesis`, uniquement dans ce contexte.
Les records de configuration imbriqués et les retours à la ligne sont
pris en charge ; `end` dans les records/commentaires/chaînes ne ferme pas
la déclaration. Les liaisons restent des constantes de configuration, pas
des expressions évaluées. Voir [la migration](../../docs/adr/0016-declarations-language-struct.md).

Si tout paraît sans couleur :

1. Vérifier **Hypomnesis** dans le sélecteur de langage en bas à droite ;
   une association utilisateur `files.associations` peut remplacer `.hyp`.
2. Vérifier que `hypomnesis.hypomnesis` est activée dans ce profil/espace
   de travail : `code --list-extensions --show-versions`.
3. Reconstruire et installer le VSIX ci-dessus, puis **Developer: Reload
   Window**. Le numéro 0.1.0 ne distingue pas les anciens builds locaux ;
   0.1.1 ajoutait les scopes de métadonnées ; 0.1.2 utilise la nouvelle syntaxe.
4. **Developer: Inspect Editor Tokens and Scopes** montre les scopes
   effectifs ; leur couleur exacte dépend du thème.

Les tests TextMate couvrent le bloc exact. Le test Extension Host ouvre
réellement ce fichier `.hyp`, vérifie association et activation, tokenise
avec la grammaire de la contribution chargée, et conserve les tests de
diagnostic/correction non enregistrée. Il remplace aussi temporairement
la déclaration par l'ancienne forme, constate son rejet syntaxique puis
rétablit la nouvelle sans diagnostic. Ce n'est pas une assertion sur les
couleurs RGB de tous les thèmes ni sur une autre fenêtre/profil déjà ouvert.

## Réglages

- `hypomnesis.pythonPath` : Python avec l'extra `lsp` ; par défaut le `.venv` du dossier
  ouvert, sinon `python3` (`python` sous Windows). Un chemin relatif est résolu depuis ce
  dossier. Ne pas ajouter d'arguments au chemin.
- `hypomnesis.languageRoot` : dossier contenant `langage.hyp` ou fichier d'entrée `.hyp`,
  relatif au dossier ouvert ou absolu. Vide : déclaration de langage dans le dossier du
  fichier ou ses parents ; pour `demo/programs/<nom>/…`, recherche aussi
  `demo/languages/<nom>/langage.hyp`.
- `hypomnesis.debounceMs` : délai de frappe, 300 ms par défaut (0 à 5 000 ms).

Un serveur est lancé par dossier dans un espace de travail multi-racines. Un changement
de réglage relance les serveurs. Le serveur lit les textes non enregistrés, y compris les
sources M2 et déclarations importées ouvertes, résout leur DAG et annule les analyses
obsolètes. Les diagnostics disparaissent après correction et à la fermeture du fichier.
Le compilateur signale la première erreur ; les erreurs d'une dépendance ou de sa déclaration
sont indiquées au début du document avec le chemin concerné. Survol, complétion et
navigation ne sont pas inclus.

Pour `demo/programs/mecanique/plaque_120x80.hyp`, la détection est automatique en ouvrant la
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
