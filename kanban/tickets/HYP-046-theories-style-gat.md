---
id: HYP-046
title: "Théories : signatures avec lois, modèles et tests de lois"
status: backlog
priority: P1
size: L
epic: M3
depends_on: [HYP-012]
labels: [python]
assignee: 
---

# HYP-046 — Théories : signatures avec lois, modèles et tests de lois

## Contexte

Étape 2 de prototypage de `docs/architecture/m3-metalangage.md` (§8) : une théorie est une signature de module enrichie de `law` ; un plugin en est un modèle (style tagless-final). Les lois sont vérifiées par tests de propriétés sur chaque modèle.

## Tâches

- [ ] Syntaxe `law nom : expr = expr` dans les signatures.
- [ ] Générer pour chaque modèle des tests Hypothesis vérifiant chaque loi.
- [ ] Exemple : théorie `Dimension` (groupe abélien) et deux modèles.

## Critères d'acceptation

- [ ] Un modèle qui viole une loi est détecté par les tests générés.
- [ ] ADR sur la syntaxe des lois.

## Fichiers concernés

- `src/hypomnesis/language/`
- `examples/`

## Références

- `docs/architecture/m3-metalangage.md`
- Conventions et définition de fini : `kanban/README.md`
