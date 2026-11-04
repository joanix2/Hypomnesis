---
title: "HYP-146 · Séparer la génération de programmes du moteur symbolique"
lane: qa
created: 2026-11-04T17:27:16+01:00
updated: 2026-11-04T18:19:29+01:00
description: "P1 · M · Architecture · paquet Codegen optionnel et CLI dédiée"
priority: P1
tags: [architecture, llm, moteur-symbolique, outillage, tests]
---

## Conversation

### user

**Ticket** HYP-146 · **Priorité** P1 · **Taille** M · **Epic** Architecture · **Labels** architecture, llm, moteur-symbolique

« en ce qui concerne tout le partie génération de code et LLM j'aimerais qu'elle soit
dans un module séparé du compilateur et du métalanguage »

Choix confirmés : paquet installable séparé `hypomnesis-codegen` dans ce dépôt et CLI
dédiée, sans commandes LLM de compatibilité dans la CLI du moteur.

#### Critères d'acceptation

- Le moteur et son extra de développement s'installent et se testent sans dépendance LLM.
- Codegen dépend du moteur, jamais l'inverse ; tests automatisés de cette frontière.
- Traduction, prompting, RAG, client, catalogue LLM, banc et graphiques sont extraits
  avec leurs tests, sans modifier les sorties de catalogue.
- Les CLI sont indépendantes ; installation, CI et documentation reflètent la séparation.
- Les fonctions symboliques et les preuves restent dans le cœur.

#### Fichiers concernés

- `packages/codegen/`
- `src/hypomnesis/cli.py`
- `pyproject.toml`
- `tests/`
- `.github/workflows/ci.yml`
- `scripts/validate.sh`
- `docs/adr/0012-codegen-separe-du-moteur.md`

### agent

Plan et checklist établis ; extraction du paquet et des commandes en cours, selon les
deux choix confirmés. Le moteur conserve la documentation structurée, les certificats,
le LSP et les capacités symboliques ; l'adaptateur M2 déterministe reste inchangé.
Pas de banc LLM réel, commit ou push prévu pour cette demande.

### user

### agent

Extraction terminée dans `packages/codegen/` : distribution `hypomnesis-codegen`,
module `hypomnesis_codegen`, ressources Jinja2 et CLI dédiée. Le cœur ne contient
plus les modules ni commandes LLM, et ses dépendances `dev` n'installent pas les
bibliothèques de génération. Les deux configurations Pyright sont indépendantes.
CI, validateurs, documentation et ADR 0012 mis à jour.

Validation : 687 tests réussis, dont 611 pour le moteur et 76 pour Codegen ; Ruff,
Pyright des deux paquets, pre-commit, Lean, audit des axiomes et certificat verts.
Les roues ont été construites depuis leurs archives source : le moteur installé
dans un environnement vierge passe ses 611 tests et Pyright sans Codegen, Ollama,
Jinja2, scikit-learn, matplotlib ou SciPy. Après ajout de la seule roue Codegen,
ses 76 tests et sa CLI passent ; le gabarit et la licence sont bien inclus.
Les instantanés du catalogue restent identiques. Graphe rafraîchi ; aucun appel
LLM réel, résultat généré dans le dépôt, commit ou push.

La nouvelle demande de couches symboliques importables et de DAG de dépendances
est suivie séparément dans HYP-147 ; elle n'est pas implémentée dans cette extraction.
Couloir inchangé.

### user

### agent

Mise à jour du Kanban demandée : passage en `qa`. Extraction et documentation
enregistrées dans `6e2962f`, avec HYP-147. Dernière validation intégrée :
735 tests (658 moteur, 77 Codegen), Python/Lean verts et paquets installés vérifiés
séparément. Checklist complète ; aucun push ni passage en `done`.

### user
