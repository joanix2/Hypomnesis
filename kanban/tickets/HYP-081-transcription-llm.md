---
id: HYP-081
title: "Transcription langage naturel → programme Hypomnesis"
status: backlog
priority: P1
size: L
epic: P7-LLM
depends_on: [HYP-080]
labels: [python, llm]
assignee: 
---

# HYP-081 — Transcription langage naturel → programme Hypomnesis

## Contexte

§14.1, §14.3 : le LLM transcrit ; sa sortie est analysée, typée, résolue, validée puis autorisée. Utiliser l'API Claude (consulter la documentation du SDK Anthropic au moment de l'implémentation pour les identifiants de modèle à jour).

## Tâches

- [ ] `llm/transcription.py` : prompt construit à partir de HYP-080 ; boucle de correction alimentée par les diagnostics du compilateur, bornée en nombre d'essais.
- [ ] Aucun code Python généré n'est jamais exécuté (§13.5).
- [ ] Jeu de tests avec réponses LLM enregistrées (pas d'appel réseau en CI).

## Critères d'acceptation

- [ ] La demande du scénario MVP (§16.2) produit un programme qui passe la vérification de types.
- [ ] Une sortie mal typée déclenche une nouvelle tentative avec le diagnostic, puis un échec propre.

## Fichiers concernés

- `src/hypomnesis/llm/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
