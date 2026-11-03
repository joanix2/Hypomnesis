---
id: HYP-040
title: "Interfaces des capacités (Observer … Resolver)"
status: backlog
priority: P0
size: M
epic: P3-EXTENSIONS
depends_on: [HYP-002]
labels: [python]
assignee: 
---

# HYP-040 — Interfaces des capacités (Observer … Resolver)

## Contexte

§6 : neuf interfaces génériques. Leur rôle type-théorique est décrit au §4.4 de `docs/architecture/m3-metalangage.md` (estimateur = proposer une métavariable, validateur = rendre un certificat, etc.).

## Tâches

- [ ] `src/hypomnesis/capabilities/` : un protocole typé par interface, indépendant du backend.
- [ ] Chaque appel rend un résultat structuré (valeur, certificat, diagnostic), jamais une exception brute.
- [ ] Docstrings reliant chaque interface au §6 et au §4.4 de la note M3.

## Critères d'acceptation

- [ ] Pyright strict sur le module ; un plugin factice de chaque type passe les tests de conformité.

## Fichiers concernés

- `src/hypomnesis/capabilities/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
