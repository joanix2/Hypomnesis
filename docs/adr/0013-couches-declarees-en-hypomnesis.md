# ADR 0013 — Couches déclarées en Hypomnesis et imports en DAG

- Statut : acceptée
- Date : 2026-11-04

## Contexte et décision

L'utilisateur veut réutiliser des couches symboliques (logique booléenne, arithmétique,
contraintes) entre langages et remplacer les manifestes JSON par des déclarations dans
le langage lui-même. Il confirme la migration sans compatibilité avec `langage.json`,
incluant toute la configuration d'exécution.

Une couche a un fichier d'entrée `.hyp`, par convention `langage.hyp` dans un dossier :

```ocaml
language exemple = {
  version = "1.0.0";
  imports = ["../booleen"; "../arithmetique/langage.hyp"];
  sources = ["regles.hyp"];
  procedure = { kind = "program"; entry = "procedure" }
}
```

Cette déclaration doit être le premier élément, unique et de premier niveau. Elle
accepte uniquement des données statiques : chaînes, entiers, booléens, listes et
records, avec clés identifiants ou chaînes. Pas d'expression évaluée, de fonction ni
d'accès aux adaptateurs pour décrire le langage. Le parseur conserve ses positions.
Les autres éléments du fichier et les fichiers `sources` définissent la couche avec
les modules existants ; le fichier d'entrée précède les sources supplémentaires.

`imports` énumère des chemins locaux relatifs au dossier du fichier d'entrée :
dossiers (résolus vers `langage.hyp`) ou fichiers `.hyp` explicites. Le graphe orienté
va de la dépendance vers son utilisateur ; ses générations topologiques sont les
couches. Les chemins canoniques dédupliquent les diamants et les alias de chemins.
Une identité dupliquée sur des fichiers distincts, un cycle ou une collision
d'exports entre paquets est une erreur, sans priorité implicite. Chaque couche est
vérifiée dans sa propre fermeture de dépendances pour ne pas profiter accidentellement
des imports d'une autre branche. Les noms qualifiés et les exports des modules
existants sont conservés ; pas de renommage d'import ni de nouvelle sémantique de visibilité.

Une bibliothèque peut omettre `procedure` ; tenter de l'exécuter comme une procédure
produit un refus explicite. Contrats, adaptateurs et permissions ne sont pas hérités
implicitement par un import : seules les définitions symboliques le sont. Les chemins
des sources, contrats, exemples et adaptateurs restent confinés à leur paquet.
Les imports, eux, peuvent viser un paquet voisin, explicitement.

Les points d'entrée/sortie Python ne sont plus décrits par des noms de fonctions
dans la configuration. Selon la précision de l'utilisateur, ils portent des
décorateurs `@sensor("id")`, `@actuator("id")`, `@environment` et `@transcriber`.
La déclaration `.hyp` énumère uniquement les modules Python autorisés avec
`adapters = ["adaptateurs/io.py"]`. Ils ne sont importés qu'à l'exécution ou à la
transcription explicite ; aucun scan implicite du dossier ou du Python installé.
Les décorateurs préservent les fonctions et n'enregistrent aucun état global ;
chaque instance de langage possède un registre d'exécution isolé.

## Conséquences

Le chargeur, la CLI et le LSP partagent le même plan de chargement. Vérifier un langage
et analyser dans l'éditeur n'évalue pas ses définitions ni ses adaptateurs.
Les erreurs conservent le fichier et la position d'origine. Le LSP tient compte des
déclarations et sources importées modifiées en mémoire.

La configuration reste un objet interne validé par JSON Schema, mais ce schéma décrit
la déclaration statique, pas un fichier de configuration utilisateur JSON.
Les démonstrations sont migrées ; `langage.json` n'est plus lu. Codegen consomme les
sources résolues sans dupliquer de résolveur. La Core IR et le runtime restent inchangés :
la déclaration est traitée avant l'élaboration, sans sémantique d'exécution.

Registre distant, contraintes de versions et renommage d'imports sont hors périmètre.
Les théories avec lois (HYP-046) pourront utiliser cette composition ultérieurement.
