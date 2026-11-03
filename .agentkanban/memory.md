# Mémoire du projet Hypomnesis

## Projet

Métalangage fonctionnel (syntaxe OCaml) pour définir des DSL métiers : connaissances, règles,
contraintes, effets contrôlés. Spécification : `docs/specification/cahier-des-charges-v0.2.md`.
Détails d'implémentation : `TECHNICAL.md`.

## Conventions

- Documentation et tickets en **français** ; code, identifiants et commentaires de code en **anglais**
  (sauf les exemples `.hyp` de domaines métiers francophones).
- Python ≥ 3.11, environnement `.venv/` ; Lean 4.35 dans `formal/` (sans Mathlib).
- **Commits réguliers** (demande explicite de l'utilisateur, prioritaire sur la règle par défaut
  d'`INSTRUCTION.md`) : un commit par étape logique terminée et vérifiée, message en français,
  terminé par la ligne `Co-Authored-By` de l'agent.
- Les hooks `pre-commit` (`.pre-commit-config.yaml`) doivent passer ; ne jamais les contourner
  (`--no-verify` interdit).
- Les tâches portent un identifiant `HYP-NNN` dans leur titre ; priorité, taille, epic et
  dépendances sont en tête du premier message `### user` de chaque tâche.
- Une tâche portant le label `humain` demande une décision de l'utilisateur.
- Tout besoin découvert hors périmètre devient une nouvelle tâche `HYP-NNN`.

## Définition de fini (toutes tâches)

- Critères d'acceptation de la tâche satisfaits.
- `.venv/bin/pytest` et `.venv/bin/pre-commit run --all-files` passent (Ruff, Pyright, YAML,
  JSON, TOML, schémas, workflows, et build Lean si `formal/` change).
- Si `formal/` est touché : `lake build` passe, aucun `sorry`, `lake env lean Audit.lean`
  n'affiche que `propext`, `Quot.sound`, `Classical.choice`.
- Si la Core IR (`src/hypomnesis/ir/core.py`) ou la sémantique de l'interpréteur change : la
  formalisation Lean est mise à jour dans le même changement (`docs/verification/strategie.md`).
- Toute propriété nouvellement prouvée est ajoutée à `docs/verification/proprietes.md` et à
  `formal/Audit.lean`.
- Toute décision structurante fait l'objet d'une ADR dans `docs/adr/`.

## Décisions clés

- ADR 0001 : prototype Python, grammaire Lark LALR(1).
- ADR 0002 : inférence HM sur l'AST, élaboration vers la Core IR ; le runtime n'exécute que la Core IR.
- ADR 0003 : noyau pur ; primitives par `external` liées à un registre natif fermé.
- ADR 0004 : contrats JSON Schema 2020-12, enveloppe indépendante du transport.
- ADR 0005 : provenance épistémique et observabilité distinctes.
- ADR 0006 (proposée) : M3 = théorie des types à deux niveaux, modale et graduée (`docs/architecture/m3-metalangage.md`).
- ADR 0007 : sémantique de référence Lean ; on prouve le vérificateur (certificats), pas le compilateur.

## État (2026-11-03)

- Faits : HYP-001 (fondations), HYP-002 (langage minimal), HYP-003 (preuves Lean initiales).
- Chemin critique vers des garanties sur les vrais programmes : HYP-020 → HYP-024 → HYP-025 → HYP-026 → HYP-027.
- Branche de travail : `phase-0-1-langage-minimal` (non poussée).
