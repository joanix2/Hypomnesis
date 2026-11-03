---
id: HYP-092
title: "Documentation de création de domaine et SDK expérimental"
status: backlog
priority: P2
size: M
epic: P8-STABILISATION
depends_on: [HYP-090, HYP-046]
labels: [doc]
assignee: 
---

# HYP-092 — Documentation de création de domaine et SDK expérimental

## Contexte

§17 phase 8 : documenter la création de domaines, publier un SDK expérimental ; hypothèse H1.

## Tâches

- [ ] Guide pas à pas : créer un domaine (théorie, modèles, plugins, contrats) sans modifier le noyau.
- [ ] Deuxième domaine indépendant (logistique ou finance) écrit en suivant le guide.

## Critères d'acceptation

- [ ] Le second domaine est créé sans aucune modification de `src/hypomnesis/` (vérifié par le diff).

## Fichiers concernés

- `docs/`
- `examples/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
