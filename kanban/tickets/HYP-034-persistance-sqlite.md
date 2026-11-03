---
id: HYP-034
title: "Persistance SQLite et import/export JSON"
status: backlog
priority: P1
size: M
epic: P2-EPISTEMIQUE
depends_on: [HYP-033]
labels: [python]
assignee: 
---

# HYP-034 — Persistance SQLite et import/export JSON

## Contexte

§7.4 : structures immuables en mémoire, journal d'événements, SQLite pour la persistance, JSON pour les échanges.

## Tâches

- [ ] Schéma SQLite du journal ; reconstruction de l'état par rejeu.
- [ ] Export et import JSON validés par schéma.
- [ ] Migrations versionnées.

## Critères d'acceptation

- [ ] Rejouer le journal persistant redonne exactement l'état en mémoire.
- [ ] Import d'un fichier invalide refusé avec le chemin de l'erreur.

## Fichiers concernés

- `src/hypomnesis/epistemics/storage.py`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
