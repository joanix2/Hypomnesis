---
title: "HYP-034 · Persistance SQLite et import/export JSON"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 2 — Moteur épistémique · dépend de HYP-033"
priority: P1
tags: [epistemique, moteur-symbolique, persistance, python]
---

## Conversation

### user

**Ticket** HYP-034 · **Priorité** P1 · **Taille** M · **Epic** Phase 2 — Moteur épistémique · **Dépend de** HYP-033 · **Labels** python

#### Contexte

§7.4 : structures immuables en mémoire, journal d'événements, SQLite pour la persistance, JSON pour les échanges.

#### Tâches proposées

- Schéma SQLite du journal ; reconstruction de l'état par rejeu.
- Export et import JSON validés par schéma.
- Migrations versionnées.

#### Critères d'acceptation

- Rejouer le journal persistant redonne exactement l'état en mémoire.
- Import d'un fichier invalide refusé avec le chemin de l'erreur.

#### Fichiers concernés

- `src/hypomnesis/epistemics/storage.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

HYP-005 adopte la v0.3 et les trois axes épistémiques. Le stockage, le rejeu
et les migrations versionnées doivent préserver existence, support, cohérence,
provenance et historique ; la migration ne doit pas réduire ces axes à un
statut unique. L'adoption documentaire ne modifie aucun format existant seule.

### user

### agent

Plan / todo / implement du lot Mac approuvé, sans sous-agent. Réutiliser
knowledge/1.0.0 et les TypeCodec fermés de l'hôte pour chaque propriété ;
ajouter un contrat de journal complet, sans exécuter de règle au rejeu.
Les événements captureront aussi l'Unknown résultant d'une invalidation :
on ne reconstruira pas un état en analysant des messages destinés à l'humain.
Le compteur de sources deviendra explicite et persistant pour éviter les
collisions après rechargement.

SQLite conservera le préfixe du journal, protégé contre UPDATE/DELETE ;
ajouts d'événements et métadonnées seront transactionnels. Migrations de
schéma SQLite versionnées, y compris upgrade non vide et refus des versions
inconnues. JSON strict, schéma puis codec puis contrôles sémantiques,
avec chemins d'erreur ; aucun import partiel ni remplacement silencieux
d'un historique divergent.

Le rejeu devra retrouver faits, sources, inconnues, retraits, journal,
compteur et contrôles de cohérence déclarés. Les invariants exécutables
resteront fournis par l'hôte et vérifiés contre leur descripteur, jamais
chargés depuis du code JSON. Les modifications directes non journalisées
de la projection seront refusées à l'export plutôt que perdues.

### user

### agent

Implémentation terminée : contrat knowledge-journal/1.0.0, vrai SQLite
transactionnel, migrations 0 → 1 → 2 et protections append-only. Le rejeu
retrouve exactement projection, inconnues, sources, retraits, événements,
compteur et contrôles déclarés ; aucun texte de méthode ou prédicat exécuté.
Les instantanés knowledge/1.0.0 et TypeCodec sont réutilisés, avec registre
partagé pour les lots d'événements.

97 tests ciblés verts, incluant la base existante : migration non vide,
échec SQL injecté au milieu d'un ajout avec rollback, préfixes divergents,
identité des sources, compteur monotone, redémarrage, imports invalides
localisés, records/options/listes et grand entier exact. 30 historiques
générés vérifient le rejeu sans mutation. Les invariants exigent leurs
liaisons hôte et ne sont pas exécutés au chargement.

Validation complète verte : linters, types, schémas, suites cœur/Codegen,
audit Lean, 86 tests Lean obligatoires et 500 termes différentiels.
QA proposée ; done humain. Aucune inférence LLM, sous-agent ou push.

### user

### agent

Validation rapide finale et graphe verts. Checklist terminée ; commit local
du jalon de persistance, sans push.

### user
