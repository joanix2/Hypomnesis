# Kanban — Hypomnesis

Tickets de développement rédigés pour être pris en charge **par des agents autant que par
des humains**. Chaque ticket se suffit à lui-même : contexte, fichiers concernés, tâches,
critères d'acceptation, références.

- Tableau : [BOARD.md](BOARD.md), généré par `python kanban/board.py`
- Tickets : [tickets/](tickets/), un fichier `HYP-NNN-slug.md` par ticket

## Champs du front-matter

| Champ | Valeurs |
|---|---|
| `id` | `HYP-NNN` |
| `status` | `backlog` · `in-progress` · `review` · `done` |
| `priority` | `P0` (chemin critique du MVP) · `P1` · `P2` · `P3` |
| `size` | `S` (< 1 jour) · `M` (1–3 jours) · `L` (> 3 jours, à redécouper si possible) |
| `epic` | voir `EPICS` dans `board.py` |
| `depends_on` | identifiants qui doivent être `done` avant de commencer |
| `labels` | `lean`, `python`, `doc`, `humain` (décision humaine requise), … |
| `assignee` | agent ou personne qui porte le ticket (obligatoire en `in-progress`) |

Les colonnes **Prêt** et **Bloqué** ne sont pas saisies : un ticket `backlog` est prêt dès que
toutes ses dépendances sont `done`.

## Protocole pour un agent

1. **Choisir** un ticket de la colonne *Prêt*, la priorité la plus haute d'abord. Ignorer
   ceux qui portent le label `humain` : ils demandent une décision du porteur du projet.
2. **Réserver** : passer `status: in-progress` et renseigner `assignee`, régénérer le tableau,
   committer ce seul changement.
3. **Travailler** sur une branche `hyp-NNN-slug`. Lire les références du ticket avant d'écrire
   du code. Rester dans le périmètre : tout besoin découvert devient un **nouveau ticket**.
4. **Livrer** : vérifier la définition de fini ci-dessous, passer `status: review`, régénérer
   le tableau, ouvrir une PR qui cite le ticket.
5. Après fusion, l'humain passe le ticket à `done`.

## Définition de fini (tous tickets)

- [ ] Tous les critères d'acceptation du ticket sont cochés.
- [ ] `pytest`, `ruff check .`, `ruff format --check .`, `pyright` passent.
- [ ] Si `formal/` est touché : `lake build` passe, aucun `sorry`, l'audit des axiomes passe
      (`lake env lean Audit.lean`).
- [ ] Si la Core IR ou la sémantique de l'interpréteur change : la formalisation Lean est mise
      à jour dans le même changement (règle de [strategie.md](../docs/verification/strategie.md)).
- [ ] Toute nouvelle propriété prouvée est ajoutée à
      [proprietes.md](../docs/verification/proprietes.md) et à `formal/Audit.lean`.
- [ ] Toute décision structurante fait l'objet d'une ADR dans `docs/adr/`.
- [ ] `python kanban/board.py --check` passe.
