---
id: HYP-102
title: "Prototype du niveau méta (λΠ-modulo, `Desc`) en Lean"
status: backlog
priority: P3
size: L
epic: M3
depends_on: [HYP-023, HYP-005]
labels: [lean, recherche]
assignee: 
---

# HYP-102 — Prototype du niveau méta (λΠ-modulo, `Desc`) en Lean

## Contexte

Étape 5 de `docs/architecture/m3-metalangage.md` (§3.2, §6.6, §7) : noyau méta en λΠ-calcul modulo réécriture et univers de descriptions avec `⌜Desc⌝ : Desc` au niveau suivant (lévitation). Chantier de recherche.

## Tâches

- [ ] Formaliser en Lean les huit primitives du §7 de la note.
- [ ] Encoder la théorie `Mechanics` et la théorie des théories ; montrer `El ⌜M3⌝ ≅ M3` au niveau suivant.
- [ ] Rapport : ce qui est réellement utilisé par les domaines (pour dimensionner le noyau).

## Critères d'acceptation

- [ ] Encodage vérifié par Lean ; rapport versionné dans `docs/architecture/`.

## Fichiers concernés

- `formal/Hypomnesis/Meta/`

## Références

- `docs/architecture/m3-metalangage.md`
- Conventions et définition de fini : `kanban/README.md`
