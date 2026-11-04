# Tickets parallèles en worktrees isolés

La CLI `scripts/parallel.py` réutilise le Kanban. Elle ne lance pas d'agent :
la conversation principale distribue les missions produites. Elle ne pousse pas,
ne change pas les couloirs et ne supprime pas les worktrees.

```bash
.venv/bin/python scripts/parallel.py --json plan HYP-044 HYP-051
.venv/bin/python scripts/parallel.py prepare HYP-044 HYP-051 \
  --directory ../hypomnesis-lot \
  --scope HYP-044=tests/unit/test_python_backend.py
.venv/bin/python scripts/parallel.py status
.venv/bin/python scripts/parallel.py record HYP-044
.venv/bin/python scripts/parallel.py integrate HYP-044
```

Le maximum par défaut est trois travaux actifs (`--limit`). `plan --label python`
filtre les labels historiques ; une sélection explicite d'identifiants reste
préférable. Les tâches humaines, bloquées, déjà affectées, sans empreinte connue
ou recouvrant une surface du coordinateur sont exclues avec leur motif.
Les globs sont traités conservativement, pas comme une preuve d'indépendance.

`prepare` exige une base propre et un Kanban committé. `--base` doit désigner
le HEAD courant pour que les métadonnées lues correspondent au code de base.
Les dépendances `qa`/`done` du Kanban committé sont considérées intégrées ;
une dépendance suivie dans ce lot doit aussi posséder un commit d'intégration
ancêtre de la base. Un succès d'agent ne débloque pas ses successeurs.

L'empreinte vient des fichiers du ticket, complétés par `--scope HYP-NNN=CHEMIN`.
Déclarer dès la préparation les tests et guides autorisés ; les modifications
hors empreinte sont refusées avant validation/intégration.
Les interfaces partagées (Session, registre natif, configuration, CI, Kanban,
documentation centrale) restent au coordinateur.

Branches, worktrees, missions, logs et attestations sont suivis sous le répertoire
Git commun `parallel/`, donc jamais versionnés. Les mutations utilisent un verrou
exclusif et des écritures atomiques. `plan` et `status` n'écrivent rien.
Après interruption de préparation, reprendre le même lot et la même destination
avec `prepare ... --resume`. Un worktree/une branche existant non réservé est refusé.

Chaque worktree doit disposer de son environnement installé **dans son propre
chemin** : ne pas partager une installation éditable pointant vers un autre
checkout. La CLI n'installe pas de dépendances. Les agents travaillent uniquement
dans leur worktree ; le premier amorçage de cet outil a été effectué manuellement.

`record` lance réellement `./scripts/validate.sh complet`, garde son log et lie
son résultat au SHA. Un nouveau commit invalide l'attestation. `--command`
permet une commande explicite pour d'autres dépôts et les tests ; elle est analysée
en arguments, jamais passée à un shell.

`integrate` exige une branche propre et une attestation courante. Il prépare
un merge sans commit, exécute la validation de la tâche sur le résultat combiné,
puis committe uniquement si la validation réussit sans modifier les sources.
Les intégrations sont séquentielles, pas nécessairement des fast-forwards.
La CLI conserve conflits et validations rouges pour diagnostic, sans reset,
abandon de merge ou résolution automatique. Toute réconciliation est explicite.
Après interruption d'intégration, inspecter l'état et Git avant de poursuivre :
un changement inattendu de HEAD est refusé, pas silencieusement adopté.

Après validation du lot, le coordinateur peut avancer `main` en fast-forward
vers la branche d'intégration, mettre les tickets en `qa`, rafraîchir Graphify,
puis éventuellement nettoyer les ressources identifiées. `done` reste humain.
