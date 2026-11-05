# ADR 0016 — Déclarations language avec struct / let / end

- Statut : acceptée par l'utilisateur (HYP-151).
- Remplace la seule syntaxe de déclaration de l'ADR 0013 ; ses règles
  de couches, de DAG, de confinement et d'I/O restent applicables.

## Contexte

La déclaration de configuration à accolades différait des modules du
métalangage. Après comparaison explicite des deux formes, l'utilisateur
a retenu `struct / let / end`, puis demandé de remplacer l'ancienne forme,
sans coexistence ni alias.

## Décision

```hyp
language arithmetique = struct
  let version = "1.0.0"
  let description = "Arithmétique entière réutilisable, sans entrée/sortie."
end
```

Le nom du langage et les clés du bloc sont des identifiants minuscules.
Chaque liaison est `let cle = valeur`, sans séparateur entre liaisons.
Les valeurs restent des données statiques : chaînes, entiers, booléens,
listes et records imbriqués. Les listes et records gardent leurs `;`,
leurs accolades et les clés de record éventuellement citées.

Ce bloc n'est ni un module exécutable ni une suite d'expressions `let` :
pas de paramètres, récursion, annotations, références, applications ou
effets. Les clés sont uniques ; elles ne créent pas de variables dans le
programme. La validation du schéma de configuration reste inchangée.

## Migration et conséquences

Remplacer les accolades extérieures par `struct` et `end`, préfixer
chaque champ extérieur par `let` et retirer ses `;`. Ne pas modifier
les records/listes imbriqués. La forme extérieure à accolades produit
désormais une erreur de syntaxe localisée attendant `struct` ; aucun
convertisseur implicite ni lecture de l'ancien manifeste JSON.

Les déclarations actives, fixtures, documentation et grammaire VS Code
sont migrées ensemble. L'ADR 0013 et les conversations historiques ne
sont pas réécrites. L'AST `LanguageItem`, le contrat de configuration,
les imports, l'isolation des adaptateurs et la Core IR ne changent pas ;
aucune extension de sémantique Lean n'est donc nécessaire.
