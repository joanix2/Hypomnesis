---
title: "HYP-140 · Mini-RAG : paires cas métier → programme"
lane: todo
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T08:56:00+01:00
description: "P2 · M · Phase 7 — Intégration LLM · dépend de HYP-138, HYP-139"
---

## Conversation

### user

**Ticket** HYP-140 · **Priorité** P2 · **Taille** M · **Epic** Phase 7 — Intégration LLM · **Dépend de** HYP-138, HYP-139 · **Labels** python, llm, rag

#### Contexte

Guider le LLM avec les exemples les plus proches de la demande, plutôt qu'avec une liste fixe. Chaque langage fournit ses paires, et le compilateur garantit qu'elles restent justes.

#### Tâches proposées

- Fichier de paires (demande, programme) dans le paquet de langage, déclaré dans le manifeste et décrit par un JSON Schema.
- Vérifier tous les programmes des paires en CI, avec le typeur et une simulation.
- Recherche simple des k paires proches : d'abord TF-IDF avec scikit-learn ; comparer ensuite aux plongements Ollama, seulement si le gain le justifie.
- Injecter les paires dans le prompt de HYP-138, en respectant le budget de taille.

#### Critères d'acceptation

- Une paire qui ne compile plus fait échouer la validation.
- Le banc compare sans exemple, exemples fixes et exemples recherchés sur le jeu réservé de HYP-139 ; le mode par défaut est choisi d'après ces mesures.
- Le moteur ne contient aucun exemple ni concept de domaine.

#### Fichiers concernés

- `src/hypomnesis/llm/`
- `src/hypomnesis/contracts/schemas/language-manifest-1.0.0.json`
- `languages/mecanique/`
- `languages/ventilation/`

#### Références

- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

**Avancement (2026-11-04).** Fait : `exemples.json` par langage (20 paires mécanique, 6 ventilation), déclaré dans le manifeste et décrit par le schéma `language-examples` ; test CI : chaque paire compile, tourne en simulation et ne recoupe aucun cas du banc ; recherche TF-IDF sur n-grammes de caractères, insensible aux nombres (`llm/retrieval.py`) ; comparaison sans exemple, exemples fixes, exemples recherchés sur les trois jeux ; défaut choisi : `catalogue+rag5`.

Mesures (détail dans l'ADR 0009) : pour un 4B, les exemples n'apportent rien de net au-dessus du catalogue (96 % → 98 %) ; pour un 1,7B ils comptent (67 % → 87-89 %), et exemples fixes ou recherchés ne se distinguent pas sur 55 cas. Les plongements Ollama ne sont donc pas justifiés pour l'instant.

Reste : injection sous budget de taille (les 5 paires sont ajoutées sans limite de longueur) et un jeu de paires plus grand, où fixes et recherchés pourraient se séparer.

### user
