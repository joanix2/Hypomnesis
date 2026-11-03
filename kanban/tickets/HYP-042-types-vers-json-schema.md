---
id: HYP-042
title: "Correspondance types Hypomnesis ↔ JSON Schema"
status: backlog
priority: P0
size: L
epic: P3-EXTENSIONS
depends_on: [HYP-041]
labels: [python, contrats]
assignee: 
---

# HYP-042 — Correspondance types Hypomnesis ↔ JSON Schema

## Contexte

§13.4 : les signatures des extensions doivent permettre de générer ou de vérifier les contrats JSON Schema ; les correspondances entre types statiques, types JSON et concepts sont explicites.

## Tâches

- [ ] Définir la correspondance (ADR) : int, float, string, bool, unit, records, variants (objet étiqueté), listes, option.
- [ ] Générer un schéma depuis un type et vérifier la compatibilité entre une signature et un schéma déclaré.
- [ ] Encodage et décodage valeur ↔ JSON.

## Critères d'acceptation

- [ ] Pour tout type supporté : `decode(encode(v)) == v` et `encode(v)` est conforme au schéma généré (test Hypothesis).
- [ ] Une signature incompatible avec le schéma du manifeste est refusée avant toute exécution.
- [ ] ADR rédigée.

## Fichiers concernés

- `src/hypomnesis/contracts/`
- `docs/adr/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
