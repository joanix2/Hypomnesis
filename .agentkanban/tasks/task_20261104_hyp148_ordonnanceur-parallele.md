---
title: "HYP-148 · Ordonnanceur local de tickets en worktrees isolés"
lane: qa
created: 2026-11-04T18:22:06+01:00
updated: 2026-11-04T18:22:06+01:00
description: "P1 · L · Outillage · sélection, préparation, suivi et intégration séquentielle"
priority: P1
tags: [git, kanban, outillage, tests]
---

## Conversation

### user

**Ticket** HYP-148 · **Priorité** P1 · **Taille** L · **Epic** Outillage · **Dépend de** HYP-009, HYP-144 · **Labels** outillage, kanban, git

Planifier plusieurs tickets symboliques en parallèle sur des worktrees séparés,
en incluant un ordonnanceur réutilisable. CLI locale, agents pilotés depuis la
conversation, maximum trois travaux actifs. Intégration séquentielle des branches
validées, arrêt au premier conflit ou échec, aucun push.

#### Critères d'acceptation

- `plan`, sans mutation, sélectionne les tickets prêts selon priorités et conflits ;
  texte/JSON explicites et déterministes. Réutiliser `scripts/kanban.py`.
- `prepare` crée branches/worktrees depuis un SHA explicite et des missions ;
  refuser base sale, références invalides, dossiers/branches existants et doubles affectations.
- `status` et `record` suivent résultats et validations attachés au SHA ; un nouveau
  commit invalide une attestation précédente. Le succès d'agent ne vaut pas intégration.
- `integrate` valide et intègre séquentiellement, s'arrête sur échec/conflit,
  ne pousse jamais et ne résout pas automatiquement les conflits.
- Exclusions conservatrices : tickets humains, bloqués, déjà affectés,
  empreinte inconnue, intersections de chemins/répertoires/globs et API réservées.
  Vérifier aussi les fichiers réellement modifiés avant intégration.
- État local ignoré, format versionné, écritures atomiques et verrou propre ;
  reprise par inspection Git/worktrees après interruption.
- Aucun reset destructif, suppression automatique ou passage en `done`.
- Tests sur dépôts Git temporaires : sélection, conflits, concurrence, reprise,
  base sale, préparation réelle, attestation périmée, intégration verte et rouge.

#### Fichiers concernés

- `scripts/parallel.py`
- `tests/tools/test_parallel.py`
- `docs/outillage/ordonnanceur-parallele.md`

### agent

Checklist produite avant implémentation. Ce premier lot est amorcé manuellement
par le coordinateur, car l'outil n'existe pas encore. Le nouvel ordonnanceur est
testé dans des dépôts temporaires, pas sur sa propre exécution.
Maximum trois sous-agents ; validations complètes sérialisées. Le coordinateur
gère tickets, mémoire, documentation centrale et Graphify ; le sous-agent ne
modifie que les trois surfaces réservées ci-dessus. Aucun SDK d'agents ajouté.

### user

### agent

CLI livrée dans `baff6ee` et intégrée après HYP-044/051. `plan`, `prepare`,
`status`, `record`, `integrate` réutilisent le Kanban et Git sans SDK.
État ignoré dans le répertoire Git commun, écritures atomiques/verrou,
préparation reprenable, empreintes et conflits conservateurs, attestations
liées au SHA et merges séquentiels validés avant commit.
Conflits, validations rouges et mutations par les validateurs restent explicites,
sans reset ni suppression automatique. Aucun changement de couloir par l'outil.

Dix-huit tests sur dépôts Git temporaires couvrent préparation réelle, deux
intégrations, conflits, échec combiné, verrou, reprise partielle, doublons,
limite active, attestations périmées, hors périmètre et dépendance non intégrée.
Validation complète verte du lot intégré (784 tests, types et Lean).
Guide dédié et documentation technique ajoutés.

Premier lot amorcé manuellement comme prévu. Les trois agents d'implémentation
et les deux relecteurs lancés n'avaient pas d'outils ; ils n'ont donc pas modifié
le code. Le coordinateur a repris les travaux dans leurs branches/worktrees,
puis validé les intégrations séquentielles. Ce lot ne constitue pas une preuve
d'exécution autonome d'agents ; la CLI prépare les missions, leur lancement
reste à la conversation dans un environnement outillé.

Les interruptions d'intégration nécessitent inspection et réconciliation explicites ;
seule la préparation dispose d'une reprise automatisée. Aucun push, pas de `done`.

### user
