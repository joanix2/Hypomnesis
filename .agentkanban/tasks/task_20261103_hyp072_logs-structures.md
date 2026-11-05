---
title: "HYP-072 · Logs structurés corrélés et expurgation"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · S · Phase 6 — Observabilité · dépend de HYP-070"
priority: P1
tags: [observabilite, outillage, python, securite]
---

## Conversation

### user

**Ticket** HYP-072 · **Priorité** P1 · **Taille** S · **Epic** Phase 6 — Observabilité · **Dépend de** HYP-070 · **Labels** python, observabilité

#### Contexte

§12.5 : logs JSON corrélés aux traces ; pas de données brutes de capteurs, de prompts LLM ni de données personnelles par défaut.

#### Tâches proposées

- Format du §12.5 ; filtre d'expurgation configurable.
- Corrélation `trace_id` et `span_id`.

#### Critères d'acceptation

- Test : un prompt LLM n'apparaît jamais dans les logs par défaut.

#### Fichiers concernés

- `src/hypomnesis/observability/logging.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan / todo / implement du lot P1 approuvé. HYP-070 est QA et committé ;
HYP-071 a passé la validation complète et termine son commit local.
Implémenter des événements JSON sur stderr, séparés de stdout CLI, avec
run/trace/span explicites et isolés par ContextVar. Aucun fournisseur de
logs global ni capture automatique des arguments/résultats.

Expurgation par défaut : prompts, payloads, données personnelles et
exceptions, y compris les structures imbriquées. Métadonnées de logs en
liste positive ; politique hôte configurable pour renforcer les champs
sensibles. Ne jamais formatter le contenu d'une exception pour le log.
Les diagnostics des exporteurs officiels doivent conserver le code HTTP
et la corrélation, pas un corps de réponse ou une exception libre.

Tests d'absence de secrets en JSON, traces et erreurs, concurrence,
désactivation, événements réels et sortie CLI JSON inchangée. Validation
complète/rapide/graphe avant QA et commit ; aucun push.

### user

### agent

Validation complète verte. Les événements JSON réels sur stderr portent
run/trace/span ; le run reste distinct lors d'un parent distant commun.
Le logger privé standard n'installe aucun provider global. Métadonnées en
liste positive, valeurs contrôlées et politique de renforcement hôte ;
prompts, payloads, champs personnels, objets arbitraires et exceptions
ne sont pas formatés. Les traces d'exception gardent seulement leur type
et des marqueurs expurgés ; l'exception originale est relancée.

Les tests vérifient les structures imbriquées/cycliques, un `__str__`
d'exception interdit, threads/tâches async, désactivation, invariance
des résultats, stdout JSON et véritable échange OTLP traces/métriques :
le prompt fictif n'apparaît ni dans les octets envoyés ni dans le corps
HTTP de refus journalisé. Le code HTTP et run/trace restent disponibles.

Frontières documentées : les métadonnées déclarées sont de confiance ;
un `print` arbitraire d'adaptateur ou un ajout volontaire via l'API SDK
brute n'est pas une collecte automatique de cette façade. Aucun appel LLM.
Passage en QA ; graphe et validation rapide avant commit local, sans push.

### user
