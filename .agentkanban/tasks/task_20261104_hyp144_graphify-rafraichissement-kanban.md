---
title: "HYP-144 · Rafraîchissement Graphify après injection du Kanban"
lane: todo
created: 2026-11-04T15:52:00+01:00
updated: 2026-11-04T15:52:00+01:00
description: "P2 · S · Outillage — défaut découvert pendant HYP-041"
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
