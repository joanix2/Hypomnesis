---
id: HYP-011
title: "Import entre fichiers"
status: backlog
priority: P2
size: M
epic: LANG
depends_on: [HYP-002]
labels: [python]
assignee: 
---

# HYP-011 — Import entre fichiers

## Contexte

La CLI charge les fichiers dans l'ordre donné ; il n'existe pas de dépendance déclarée entre fichiers (§4.1 « Modules et imports »). `examples/mechanics/plate.hyp` dépend implicitement de `units.hyp`.

## Tâches

- [ ] Concevoir la syntaxe (ADR) : par exemple, un fichier `units.hyp` définit le module `Units` et `open Units` le charge à la demande.
- [ ] Résoudre les chemins relativement au fichier et à un chemin de recherche ; détecter les cycles.
- [ ] Charger chaque fichier une seule fois par session.

## Critères d'acceptation

- [ ] `hypomnesis run examples/mechanics/plate.hyp` fonctionne seul.
- [ ] Un import circulaire donne une erreur claire.
- [ ] ADR rédigée.

## Fichiers concernés

- `src/hypomnesis/session.py`
- `src/hypomnesis/cli.py`
- `examples/mechanics/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
