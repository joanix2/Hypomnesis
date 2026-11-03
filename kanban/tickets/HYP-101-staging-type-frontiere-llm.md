---
id: HYP-101
title: "Code typé `⇑A` pour la frontière LLM"
status: backlog
priority: P3
size: L
epic: M3
depends_on: [HYP-081, HYP-012]
labels: [python]
assignee: 
---

# HYP-101 — Code typé `⇑A` pour la frontière LLM

## Contexte

§5.4 de `docs/architecture/m3-metalangage.md` : une sortie LLM est de la syntaxe non typée ; seul l'élaborateur produit du code typé `⇑A`, et seul ce code peut être épissé. Le pipeline du §14.3 devient une chaîne de modalités.

## Tâches

- [ ] Type `Syntax.t` (non typé) et `'a code` (typé) ; `elaborate : Syntax.t -> ('a code, diagnostic) result`.
- [ ] Rendre impossible la construction de `'a code` hors de l'élaborateur.

## Critères d'acceptation

- [ ] Aucun chemin, dans l'API, ne mène d'une chaîne LLM à l'exécution sans passer par `elaborate` (vérifié par revue et test).

## Fichiers concernés

- `src/hypomnesis/llm/`
- `src/hypomnesis/language/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
