---
id: HYP-090
title: "Scénario MVP principal : plaque de bout en bout"
status: backlog
priority: P0
size: L
epic: P8-STABILISATION
depends_on: [HYP-054, HYP-052, HYP-055, HYP-063, HYP-082]
labels: [python, exemple]
assignee: 
---

# HYP-090 — Scénario MVP principal : plaque de bout en bout

## Contexte

§16.2 : « Crée une plaque de 120 × 80 mm, estime son épaisseur, vérifie sa validité et exporte sa géométrie. » Dix étapes.

## Tâches

- [ ] Enchaîner transcription, compilation, normalisation des dimensions, estimation, résolution, validation, commande d'export, résultat JSON.
- [ ] Actionneur logiciel d'export de géométrie (fichier).
- [ ] Trace et métriques enregistrées.

## Critères d'acceptation

- [ ] Test de bout en bout avec réponse LLM enregistrée.
- [ ] Chaque étape du §16.2 est identifiable dans la trace et la provenance.

## Fichiers concernés

- `examples/mechanics/`
- `tests/e2e/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
