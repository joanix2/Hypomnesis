---
title: "HYP-142 · Fine-tuning de petits modèles sur un langage"
lane: todo
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T08:56:00+01:00
description: "P3 · L · Phase 7 — Intégration LLM · dépend de HYP-141"
---

## Conversation

### user

**Ticket** HYP-142 · **Priorité** P3 · **Taille** L · **Epic** Phase 7 — Intégration LLM · **Dépend de** HYP-141 · **Labels** python, llm, fine-tuning, idée

#### Contexte

Tester si un petit modèle affiné égale, sur un langage donné, un modèle plus gros guidé par le prompt et le mini-RAG. La machine de référence a une RTX 3060 de 12 Go. Le résultat doit justifier la complexité : c'est une expérience, avec une issue négative possible.

#### Tâches proposées

- Entraîner un adaptateur LoRA sur `qwen3:4b-instruct` ou un modèle comparable, avec des bibliothèques courantes (PEFT, éventuellement Unsloth).
- Convertir le résultat au format GGUF et le servir avec Ollama, pour réutiliser le banc sans changement.
- Comparer sur le jeu réservé : modèle de base, base + prompt + RAG, modèle affiné.
- Mesurer aussi la généralisation à un langage non vu et le coût de réentraînement quand le langage évolue.
- Isoler les dépendances d'entraînement dans un groupe optionnel de `pyproject.toml`.

#### Critères d'acceptation

- L'entraînement tourne sur 12 Go de VRAM et se relance à partir d'une commande documentée.
- Un rapport compare justesse, réparations, latence et mémoire, avec intervalles de confiance.
- Le rapport conclut par une décision : adopter ou abandonner, avec les chiffres à l'appui.

#### Fichiers concernés

- `src/hypomnesis/llm/`
- `pyproject.toml`

#### Références

- Conventions et définition de fini : `.agentkanban/memory.md`
