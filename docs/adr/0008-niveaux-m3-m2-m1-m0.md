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
- Le moteur offre des **procédures génériques** (`Resolver`, §6), configurées par le manifeste :
  `constrained-design` et `feedback-loop`. Il les exécute sans connaître aucun domaine. Les
  contraintes sont déclarées en Hypomnesis avec le type `Problem.problem` de la bibliothèque
  standard.
- Un **test d'architecture** (`test_engine_contains_no_domain`) échoue si un nom de domaine
  apparaît dans `src/hypomnesis/`.

## Conséquences

- La commande `hypomnesis lancer LANGAGE [PROGRAMME]` remplace les démonstrations dédiées.
- Ajouter un domaine, c'est ajouter un dossier dans `languages/`, sans toucher au moteur.
- Étape suivante : remplacer les procédures figées par des procédures M1 écrites en Hypomnesis,
  dont les effets sont des valeurs (HYP-060). Les deux procédures actuelles en deviendront des
  cas particuliers.
