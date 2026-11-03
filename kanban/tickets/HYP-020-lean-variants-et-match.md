---
id: HYP-020
title: "Lean F1a : variants et `match` général"
status: backlog
priority: P0
size: L
epic: FORMEL
depends_on: [HYP-003]
labels: [lean]
assignee: 
---

# HYP-020 — Lean F1a : variants et `match` général

## Contexte

Le fragment Lean (`formal/Hypomnesis/Core/`) ne couvre ni les variants ni le filtrage général, alors que la Core IR Python (`Construct`, `Match`, motifs `PCtor`, `PTuple`, `POr`, `PAlias`) les utilise partout, listes comprises. C'est le prérequis du pont de certificats.

## Tâches

- [ ] Syntaxe : déclarations de types variants (un environnement de déclarations Σ), `construct`, `match` avec motifs.
- [ ] Typage des motifs (contexte produit par un motif) et des `match`.
- [ ] Évaluation : filtrage premier bras gagnant ; `Match_failure` devient un résultat distinct de `stuck`.
- [ ] Étendre `eval_safe` : un terme bien typé ne rend jamais `stuck` (il peut rendre `matchFailure`).
- [ ] Étendre `typeOf` et ses preuves de correction et complétude ; mettre à jour la table de correspondance de `Syntax.lean`.

## Critères d'acceptation

- [ ] `lake build` passe ; aucun `sorry` ; audit des axiomes inchangé.
- [ ] `docs/verification/proprietes.md` : P1–P6 annoncés pour le fragment étendu.
- [ ] Les listes du prélude s'expriment dans le fragment (`[]` et `::` comme variant).

## Fichiers concernés

- `formal/Hypomnesis/Core/`
- `formal/Audit.lean`

## Références

- `docs/verification/proprietes.md`
- `docs/verification/strategie.md`
- Conventions et définition de fini : `kanban/README.md`
