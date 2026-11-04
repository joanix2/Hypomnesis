---
title: "HYP-053 · Vérificateur de certificats de solveur (+ preuve Lean)"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 4 — Raisonnement hybride · dépend de HYP-052"
priority: P1
tags: [certification, lean, moteur-symbolique, python, solveurs, tests, validateurs]
---

## Conversation

### user

**Ticket** HYP-053 · **Priorité** P1 · **Taille** M · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-052 · **Labels** python, lean

#### Contexte

§4.5 de `docs/architecture/m3-metalangage.md` : seul le noyau rend un fait `Derived`. Un modèle Z3 est accepté après vérification qu'il satisfait toutes les contraintes, par évaluation indépendante de Z3.

#### Tâches proposées

- Évaluateur de contraintes de la Problem IR sur une affectation.
- Lean : modéliser cet évaluateur et prouver qu'un modèle accepté satisfait les contraintes.

#### Critères d'acceptation

- Un modèle volontairement faux est refusé.
- Théorème Lean ajouté à l'audit.

#### Fichiers concernés

- `src/hypomnesis/engine/`
- `formal/Hypomnesis/Problem/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

HYP-052 est en QA. L'évaluateur indépendant check_assignment et sa
revérification par solution_value existent déjà ; aucune seconde pile de
solveur n'est nécessaire. Formaliser la projection de faisabilité de la
Problem IR normalisée : domaines real/int/bool, bornes, choix discrets et
sommes linéaires rationnelles exactes. Séparer la relation sémantique de
l'évaluateur exécutable et prouver qu'un modèle accepté satisfait tous
les domaines et contraintes, sans optimalité ni preuve d'unsat.

Relier le modèle à Python par un corpus déterministe généré, valeurs
adversariales et vrais modèles Z3. Le rendu de ces données en termes Lean
reste une frontière testée, pas une preuve de raffinement Python. Tester
aussi qu'un faux modèle de plugin ne peut reprendre la continuation ni
créer un fait Derived. Pas de promotion automatique du support : un modèle
vérifié est faisable, pas une observation ni une prémisse physique.

### user

### agent

Projection de faisabilité implémentée en Lean : noms connus, domaines
real/int/bool, bornes, choix et contraintes linéaires rationnelles exactes.
La relation inductive LinearValue est distincte du fold exécutable.
Correction et complétude de l'évaluation et du vérificateur sont prouvées,
ajoutées à l'audit et au catalogue P27–P28, sans `sorry` ni axiome maison.

413 cas concordent entre Python et le vrai modèle Lean exécutable :
336 affectations générées/altérées, 29 frontières exactes et 24 vrais
modèles Z3 accompagnés de leurs altérations. Les cas incluent 1/3, entiers
de plus de 64 bits, décimaux, sommes vides, coefficients négatifs, booléens
0/1 dans les sommes, bornes/choix, types erronés, NaN/infinis, noms absents
et supplémentaires. Les deux opérations Solve refusent une fausse
affectation avant une continuation demandant un fait Derived ; le fait
d'entrée reste intact. Pas de nouvel enregistrement automatique.

47 tests ciblés initiaux verts, puis 15 tests ciblés de correspondance et
continuations après ajout des gardes. Validation complète verte : linters,
types, tests moteur/Codegen, build et audit Lean, 86 tests obligatoires du
checker/différentiel/modèles. Les 500 termes différentiels passent encore.
La correspondance de ce modèle avec Python et le rendu des données restent
testés, pas prouvés ; ni diagnostic textuel, JSON, optimum, unsat, physique
ou planification ne sont certifiés par ces théorèmes. QA proposée à l'humain.

### user

### agent

Validation rapide avant commit et graphe final verts. Jalon prêt à
committer ; aucun push.

### user
