---
title: "HYP-030 · Modèle de données des connaissances"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-04T19:25:09+01:00
description: "P0 · M · Phase 2 — Moteur épistémique · dépend de HYP-002"
priority: P0
tags: [epistemique, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-030 · **Priorité** P0 · **Taille** M · **Epic** Phase 2 — Moteur épistémique · **Dépend de** HYP-002 · **Labels** python

#### Contexte

§7 du cahier des charges et §4.2–4.3 de `docs/architecture/m3-metalangage.md`. Une connaissance est un fait (valeur typée d'un concept) avec une provenance. Les statuts se lisent selon trois axes : existence (connu ou métavariable), support (`Observed` ⊑ `Estimated` ⊑ `Defaulted` ⊑ `Hypothesis`) et cohérence. Si HYP-005 rejette cette décomposition, revenir aux sept statuts de la v0.2.

#### Tâches proposées

- Créer `src/hypomnesis/epistemics/knowledge.py` : structures immuables `Fact`, `Observation`, identifiants stables.
- Représenter `Unknown` par une métavariable (voir HYP-032) et non par une valeur sentinelle.
- Sérialisation JSON (schéma versionné dans `contracts/schemas/`).

#### Critères d'acceptation

- Structures gelées, testées ; aller-retour JSON validé par schéma.
- Docstring reliant chaque statut du §7.1 à sa représentation.

#### Fichiers concernés

- `src/hypomnesis/epistemics/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- `docs/architecture/m3-metalangage.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Arbitrage humain HYP-005 du 4 novembre 2026 : les trois axes sont adoptés.
La réserve initiale de retour aux sept statuts est levée ; utiliser
`docs/specification/cahier-des-charges-v0.3.md` §7.1 comme référence.
Existence, support et cohérence sont indépendants ; `Derived` désigne la
justification et non un grade. Cette décision n'adopte pas toute l'ADR 0006.

### user

continue

### agent

Reprise directe après HYP-005, sans sous-agent. Les structures et la base
existent déjà (HYP-008 et démonstrateur) : ne pas les réimplémenter.
Compléter leur immuabilité profonde, les validations et une Observation
explicite. Garder les signatures historiques de Fact et de KnowledgeBase.

La frontière JSON réutilisera TypeCodec pour contrôler les valeurs par un
type Hypomnesis fermé, y compris records, variants et listes ; un contrat
knowledge/1.0.0 portera identité logique, provenance et métadonnées.
Le type attendu est fourni par l'hôte, jamais accepté aveuglément depuis JSON.
Unknown reste une métavariable ; propositions/résolution complète sont HYP-032.
Pas de nouveau planificateur, stockage SQLite ou politique de conflit dans ce lot.

#### Implémentation et vérification

- Fact capture les valeurs composites dans un instantané immuable ; les lectures
  renvoient des conteneurs détachés. La représentation nominale du runtime est
  conservée et les scalaires bool/int/float restent distingués.
- Source et Unknown valident leurs métadonnées. Observation relie un fait
  directement observé et sa source, dont l'identifiant est préservé.
- Le contrat fermé knowledge/1.0.0 et `epistemics/serialization.py` utilisent
  TypeCodec pour l'authentique frontière JSON textuelle : le type attendu est
  contrôlé et les valeurs sont vérifiées dans les deux sens.
- Les cinq constructeurs de provenance sont préservés ; aucun grade n'est
  importé comme une autorité de confiance. Les prémisses répétées restent
  autorisées, avec leur signification antérieure en semi-anneau.
- Les données cycliques, objets non supportés et nombres non finis sont refusés
  explicitement. Les échecs de construction ne polluent pas faits/sources/journal.

45 nouveaux tests couvrent les instantanés, les identités, les invariants,
les erreurs, les scalaires et types structurés, avec un aller-retour généré
par Hypothesis. Validation complète verte : **830 tests (753 cœur, 77 Codegen)**,
Ruff, Pyright, schémas, build/audit Lean et vérificateur de certificats.
L'exemple du guide `docs/architecture/connaissances.md` est exécuté avec succès.

Limites assumées : la base reste mutable, les identifiants de source restent
locaux à la base, et un fait dérivé exige le contexte de ses sources pour
évaluer son support. Ce n'est pas un format d'export complet de base, un solveur
de métavariables ni une preuve Lean nouvelle. HYP-030 passe en QA, pas en done.

### user

tout les ticket en todo qui sont des hypothèses met les dans hypothèses

### agent

Revue des tickets en `todo` : déplacement de **11 propositions** dans
`hypothese`, sans changement de priorité, dépendances ou critères historiques.

- HYP-046 : théories GAT et lois, piste de prototypage M3 non adoptée.
- HYP-100 à HYP-103 : grades dans le typeur, staging typé, noyau méta et
  substituabilité des modèles ; architecture de l'ADR 0006 encore proposée.
- HYP-110 à HYP-113 : idées de DSL IA, CAO, Applications et DREAL dont les
  périmètres et choix restent ouverts.
- HYP-141 et HYP-142 : distillation et expérience de fine-tuning, étiquetées
  idées, dont le bénéfice et l'adoption restent à établir.

HYP-149 y était déjà : **12 hypothèses au total**. Aucune checklist associée
aux onze tickets déplacés n'existe, donc aucun couloir de checklist à modifier.
Les tâches d'implémentation, de test et les obligations de preuve déjà retenues
restent en todo ; parler d'une hypothèse épistémique dans leur contenu ne suffit
pas à en faire une proposition architecturale non adoptée.

Vérifications : 103 tickets valides, aucune de ces propositions dans les tâches
prêtes, dépendances conservées. HYP-092 reste notamment bloqué par HYP-046 :
son déplacement ne vaut pas achèvement ni adoption. Aucun ticket en cours
ou validé n'a changé de couloir.

### user
