---
title: "HYP-067 · Lean F5c : dry-run sans dispatch, même terme dans les trois modes"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Vérification formelle (Lean) · dépend de HYP-064, HYP-065"
priority: P1
tags: [effets, lean, moteur-symbolique]
---

## Conversation

### user

**Ticket** HYP-067 · **Priorité** P1 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-064, HYP-065 · **Labels** lean

#### Contexte

§10.3 : la logique métier ne dépend pas du mode.

#### Tâches proposées

- Prouver : le handler dry-run ne produit aucun `dispatch`.
- Prouver : les trois handlers interprètent le même terme ; la simulation et la production ne diffèrent que par les réponses des opérations.

#### Critères d'acceptation

- Théorèmes sans `sorry`, ajoutés à l'audit.

#### Fichiers concernés

- `formal/Hypomnesis/Effects/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

HYP-064 et HYP-065 sont en QA. Plan/checklist avant preuve : formaliser
un arbre d'effets à continuations typées (Observe, Act, Solve, Record,
Retract, Note), un état hôte explicite et un budget d'opérations.
Le mode n'appartient pas au terme. Les réponses Act portent état et
résultat optionnel, comme le JSON du runtime, et peuvent donc changer
la branche suivante sans réécriture du programme.

Prouver l'absence de handoff production en dry-run et simulation pour
tous termes/budgets, puis l'effacement vers un unique fold du terme et
l'égalité des résultats lorsque les réponses/transitions hôte coïncident.
Tester le modèle exécutable contre les modes réels, refus, échéance et
continuations dépendant des réponses. La correspondance avec Python reste
testée, pas un théorème de raffinement de l'interpréteur ou de ses adaptateurs.
Les retries/acquittements restent dans HYP-066, sans nouvelle promesse
d'unicité physique.

### user

### agent

Implémentation vérifiée : arbre d'effets à continuations typées, état hôte
explicite, budget d'opérations et trois handlers du même terme. Les six
théorèmes principaux sont ajoutés à l'audit, sans `sorry` ni nouvel axiome
maison (propext, et Quot.sound pour l'extensionalité).

La correspondance exécutable couvre 24 combinaisons mode/permission/délai/
validité de réponse, 15 préfixes bornés et le même programme M1 dans les
trois modes. Son IR annotée est identique ; sa continuation dépend de l'état
réel retourné. Le fichier géométrique et le span actuator.execute
n'apparaissent qu'en production. Une garde interdit le skip si Lean est
obligatoire en CI des preuves ou dans validate.sh lean/complet.

Les 9 tests ciblés passent. Validation complète verte : linters, types,
tests moteur et Codegen, build Lean, audit et 77 tests obligatoires du
checker/différentiel/modèles. Le différentiel a exécuté 500 exemples
passants, zéro échec. Graphe AST rafraîchi sans appel LLM.

Limites conservées : callbacks hôtes et fidélité complète au runtime Python
non prouvés ; aucune égalité inconditionnelle entre résultats simulés et
réels. Passage en QA pour revue humaine, pas en done.

### user

### agent

Validation rapide avant commit et rafraîchissement final du graphe verts.
Jalon prêt à committer ; aucun push.

### user
