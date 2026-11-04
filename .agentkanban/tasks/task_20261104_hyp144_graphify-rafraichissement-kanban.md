---
title: "HYP-144 · Rafraîchissement Graphify après injection du Kanban"
lane: qa
created: 2026-11-04T15:52:00+01:00
updated: 2026-11-04T18:19:29+01:00
description: "P2 · S · Outillage — défaut découvert pendant HYP-041"
priority: P2
tags: [graphify, kanban, outillage]
---

## Conversation

### user

**Ticket** HYP-144 · **Priorité** P2 · **Taille** S · **Epic** Outillage · **Labels** graphify, kanban

Fiche de suivi du défaut hors périmètre découvert pendant HYP-041 ; plan et checklist à produire
avant toute implémentation.

### agent

Défaut hors périmètre découvert lors de HYP-041, non corrigé ici.

Après un `graphify update .` réussi, puis `python scripts/kanban.py graph` réussi,
un nouveau `./scripts/validate.sh graphe` échoue lors du rafraîchissement Graphify :

```text
[graphify] WARNING: Refusing to overwrite — saved semantic node(s) are missing
from the new graph: kanban_path_src_hypomnesis_engine_registry_py.
Nothing to update or rebuild failed — check output above.
```

Le garde-fou préserve le graphe existant. L'injection du Kanban seule fonctionne encore :
`.venv/bin/python scripts/kanban.py graph`.
Les validations rapide et complète de HYP-041 restent vertes ; ce défaut ne touche pas
le registre ni la CLI et ne bloque pas leur vérification utilisateur.

À planifier : comprendre l'interaction entre les nœuds de chemin synthétiques du Kanban
et leur remplacement par des nœuds de code réels, puis permettre des rafraîchissements
répétés sans perte de données sémantiques. Ne pas contourner le garde-fou de Graphify.
Reproduction attendue : rafraîchir → injecter → rafraîchir au moins deux fois.

### user

### agent

Implémentation autorisée avec HYP-007 et HYP-004. Plan : Graphify déduplique un nœud
synthétique portant un chemin nu avec le fichier AST réel, puis son garde-fou signale
la perte de l'identifiant sémantique. Les chemins Kanban deviennent des documents
explicitement nommés « Chemin Kanban : … », avec `referenced_path` séparé. Le mode
`graphe` réinjecte d'abord les métadonnées pour migrer les anciennes représentations,
puis reconstruit et réinjecte les relations. Aucun garde-fou Graphify n'est désactivé.
Checklist créée ; tests de non-régression et deux cycles réels prévus.

### user

### agent

Correctif implémenté et validé. Deux cycles réels `validate.sh graphe` consécutifs
réussissent, sans désactivation du garde-fou ni appel LLM. Le graphe reconstruit contient
3 392 nœuds, sans identifiant dupliqué ni relation pendante ; les 69 chemins synthétiques
portent leur libellé distinct et leur chemin explicite. Les fichiers AST disponibles
restent les cibles directes des relations `touches`.

Tests d'outillage : 20 réussis, dont migration d'une ancienne représentation,
remplacement par un vrai nœud-fichier et réinjection répétée. Validation complète verte :
652 tests, linters, Pyright, schémas, Kanban, compilation Lean, audit des axiomes et
vérificateur de certificats. Documentation technique et checklist mises à jour.
Couloir laissé à l'utilisateur ; aucun passage en `done`.

### user

### agent

Contrôle final : ajout de trois tests du mode `graphe` (graphe absent, migration avant
reconstruction, arrêt si migration échoue). Le lot final passe 655 tests et l'intégralité
de `validate.sh complet`. Le graphe final a été rafraîchi à nouveau avec succès.

### user

### agent

Mise à jour du Kanban demandée : passage en `qa`. Correctif et tests enregistrés
dans `9e70271`, rafraîchissements répétés réussis. La validation intégrée suivante
sur `6e2962f` est également verte (735 tests et Lean). Checklist complète ;
aucune clôture humaine ni publication distante revendiquée.

### user
