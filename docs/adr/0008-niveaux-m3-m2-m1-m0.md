# ADR 0008 — Séparation stricte des niveaux M3, M2, M1, M0

- **Statut :** acceptée
- **Date :** 2026-11-03

## Contexte

Le premier démonstrateur avait mis un domaine (plaque, ventilation) et sa logique métier
(estimateurs, contraintes, orchestration) dans `src/hypomnesis/`, en Python. Cela contredit
OBJ-10 et le principe de l'architecture : un moteur à métalangage (M3) qui permet de décrire des
langages (M2), dans lesquels on écrit des programmes (M1) qui produisent des résultats (M0).

## Décision

| Niveau | Rôle | Emplacement | Peut dépendre de |
|---|---|---|---|
| M3 | moteur, métalangage, bibliothèque standard, procédures génériques | `src/hypomnesis/` | rien de M2, M1 ou M0 |
| M2 | langages métier : sources Hypomnesis, contrats, adaptateurs, manifeste `langage.json` | `languages/<langage>/` | API de M3 |
| M1 | programmes écrits dans un langage M2 | `programs/<langage>/` | types et fonctions de leur langage |
| M0 | résultats : rapports, fichiers produits, journaux | `sortie/` (non versionné) | — |

- La **logique métier** (concepts, règles, estimateurs, contraintes, contenu des commandes) est
  écrite en Hypomnesis dans le langage M2. Le Python d'un langage M2 se limite aux
  **adaptateurs** vers le monde extérieur (actionneurs, capteurs, substituts de LLM). Ils sont
  chargés uniquement depuis le paquet du langage.
- Les **procédures** sont écrites en Hypomnesis, dans le langage (M2) ou le programme (M1) :
  ce sont des valeurs de type `'a Effect.t` (bibliothèque standard) que le moteur interprète
  (`engine/procedure.py`). Les opérations sont génériques : observer un capteur déclaré, agir via
  le dispatcher, résoudre un `Problem.problem`, enregistrer ou retirer une connaissance. Seul le
  moteur crée des faits « observés ».
- Un **test d'architecture** (`test_engine_contains_no_domain`) échoue si un nom de domaine
  apparaît dans `src/hypomnesis/`.

## Conséquences

- La commande `hypomnesis lancer LANGAGE [PROGRAMME]` remplace les démonstrations dédiées.
- Ajouter un domaine, c'est ajouter un dossier dans `languages/`, sans toucher au moteur.
- Mise à jour (HYP-060) : les procédures figées d'abord prévues dans le moteur (`constrained-design`,
  `feedback-loop`) ont été supprimées. Elles sont désormais écrites en Hypomnesis dans les langages
  (`Plaque.concevoir`, `Ventilation.reguler`).
