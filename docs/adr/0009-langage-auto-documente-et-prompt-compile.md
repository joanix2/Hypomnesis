# ADR 0009 — Langage M2 auto-documenté et prompt LLM compilé

- **Statut :** proposée
- **Date :** 2026-11-04

## Contexte

La traduction langage naturel → programme M1 par un LLM local reposait sur un prompt qui collait
le **source brut** du langage M2 et un programme d'exemple. Trois défauts, mesurés au banc :

- le modèle voit les règles internes et peut appeler des procédures qui ne devraient pas être
  exposées (cas m11 : `reviser_par_mesure` appelé seul, échec à l'exécution) ;
- les conventions d'un programme M1 (la demande se nomme `demande`, le premier champ d'un record est
  qualifié par son module) ne sont écrites nulle part ;
- les unités, le sens de `None` et le choix entre deux procédures voisines sont dans des
  commentaires que le modèle ne lit pas comme des consignes.

## Décision

Un langage M2 **se documente lui-même**, dans l'esprit des descriptions d'un schéma GraphQL (pas
dans sa syntaxe), et le moteur **compile** cette documentation en prompt.

1. **Commentaires de description `(** … *)`** placés juste avant une déclaration (module, valeur,
   type, champ). Ce sont des commentaires ordinaires pour la grammaire : ils n'ont aucun effet
   sémantique. `language/docs.py` les rattache par la **position** de la déclaration dans l'AST,
   sans jeton dans la grammaire LALR (proposition de HYP-137).
2. **Balises `@nom texte`**, ouvertes : `@quand`, `@pas_quand`, `@unité`, `@défaut`, `@exemple`,
   `@note`, `@squelette` (un programme M1 type, rendu en bloc de code). Une balise inconnue est
   affichée sous son nom. Le sens des balises appartient à l'auteur du langage ; le moteur n'en
   connaît aucune par son contenu.
3. **Catalogue** (`llm/describe.py`, gabarit Jinja2 `llm/templates/catalogue.md.j2`) : les
   éléments *documentés*, avec les types déduits par le typeur (jamais recopiés à la main), les
   descriptions et les balises. Un élément non documenté reste hors du prompt, comme un champ privé.
   Sortie déterministe. Un langage sans documentation retombe sur son source.
4. **Paires d'exemples** `exemples.json` (manifeste, JSON Schema `language-examples`) : demande →
   programme. Les tests vérifient qu'elles compilent, tournent en simulation et ne recoupent aucun
   cas du banc. `ragN` montre au modèle les N paires les plus proches (TF-IDF sur n-grammes de
   caractères, insensible aux nombres) sous forme de tours de conversation.
5. **Stratégies composables** (`llm/prompting.py`, `--strategie`) : `source`, `catalogue`,
   `programmes`, `tirsN`, `ragN`. `base` = prompt historique. **Défaut : `catalogue+rag5`.**
6. **Description obligatoire** (HYP-137). `load_language` (langages M2 seulement, pas les programmes
   M1) refuse un langage dont un élément **public** (module, type, champ, constructeur, valeur) n'a
   pas de description : `MissingDescriptionError` (`engine/language.py`, sous-classe de
   `HypomnesisError` et de `LanguageError`) nomme l'élément qualifié, le fichier et la position
   (`strict=False` pour les langages jouets des tests). *Public* = aucun composant du nom qualifié ne
   commence par `_` (sans attendre les signatures de modules, HYP-012, qui pourront restreindre).
   - Balise **`@interne`** : élément décrit mais **non publié** dans le catalogue ni dans `decrire`.
     Il doit être décrit ; ses membres (champs, constructeurs, éléments d'un module) ne le sont pas.
   - Balise **`@discret`** (membre de type) : le champ ou constructeur reste listé (nom et type) sans
     sa description. Elle permet de décrire un champ sans changer le texte du prompt mesuré.
   - Un constructeur se décrit par un `(** … *)` placé avant `| Ctor`, sur une ligne distincte de
     celle de son type ; un membre écrit sur la ligne du type ne peut pas porter de description.
7. **Détection des commentaires par le lexeur** (`parser.lex`, `Lark.lex(dont_ignore=True)`) et non
   par regex : un `(**` dans une chaîne ou dans un commentaire ordinaire n'est pas une description.
   Les commentaires restent non imbriqués (comme le lexeur). `lexer_callbacks` a été écarté : l'état
   par analyse serait partagé par l'analyseur mis en cache ; `lex` n'a pas d'état.

## Mesures

Banc `demo/languages/*/benchmark.json`, trois jeux : *dev* (15 cas, les anciens), *test* (20, réservé) et
*hard* (20, nombres en lettres, ordre inversé, unités mixtes, négations…), soit 55 cas.
Température 0, contexte 6144, une seule génération (sans réparation) sauf mention. Métrique :
programme **correct au premier essai** (il compile, s'exécute en simulation et porte les bonnes
valeurs). Un record écrit directement dans l'appel vaut la variable `demande` attendue.

| Modèle | Prompt | Correct 1er essai | Prompt (car.) | Temps / cas |
|---|---|---|---|---|
| qwen3:1.7b | base (historique) | 30 % (17/55) | 7 577 | 0,7 s |
| qwen3:1.7b | catalogue | 67 % | 4 447 | 0,5 s |
| qwen3:1.7b | catalogue + 3 exemples fixes | 89 % | 5 165 | 0,5 s |
| qwen3:1.7b | **catalogue + 5 exemples proches** | **87 %** | 5 704 | 0,6 s |
| qwen3:4b-instruct-2507 | base (historique) | 85 % (47/55) | 7 577 | 1,0 s |
| qwen3:4b-instruct-2507 | source brut annoté | 80 % | 9 638 | 1,1 s |
| qwen3:4b-instruct-2507 | 5 exemples proches seuls | 87 % | 2 322 | 1,4 s |
| qwen3:4b-instruct-2507 | catalogue | 96 % (53/55) | 4 447 | 0,9 s |
| qwen3:4b-instruct-2507 | **catalogue + 5 exemples proches** | **98 % (54/55)** | 5 704 | 1,0 s |
| qwen3.5:9b | catalogue | 98 % (54/55) | 4 447 | 4,2 s |

Avec deux réparations par les diagnostics, le 4B instruct passe à 98 % (54/55) avec le catalogue et
reste à 85 % avec le prompt historique : les réparations corrigent les programmes qui ne compilent
pas ou ne s'exécutent pas, pas ceux qui sont bien formés mais faux.

À lire avec prudence : 55 cas ne séparent pas 96 % de 98 %. Les conclusions solides sont :

- **la documentation du langage fait l'essentiel du gain** (85 % → 96-98 % pour un 4B). Le catalogue
  seul est 41 % plus court que le prompt historique, le défaut (avec 5 exemples) 25 % plus court ; un
  4B sans raisonnement suffit ;
- **les exemples comptent surtout pour les très petits modèles** : +20 points pour un 1,7B, rien de
  net pour un 4B ; exemples fixes et exemples recherchés ne se distinguent pas ;
- le source brut, même annoté, fait moins bien que le catalogue ; les exemples seuls (sans description
  du langage) ne suffisent pas.

Un modèle « thinking » (`qwen3:4b`, variante 2507-thinking) ne peut pas désactiver son raisonnement :
~3 000 jetons et 37 s par cas pour un programme de 100 jetons. Il est exclu du banc.

## Conséquences

- Écrire un langage M2 demande de le documenter ; la qualité du prompt devient celle de ces
  descriptions. La description est **obligatoire** (HYP-137, voir la décision 6).
- Les exemples publiés par un langage doivent rester justes : ils sont rejoués par la suite de tests.
- Dépendances ajoutées : `jinja2`, `scikit-learn` (extra `llm`, inclus dans `dev`).
- Le retrieval lexical suffit ici ; des plongements Ollama ne se justifient que si un langage montre
  un écart que le lexical n'explique pas (HYP-140).

## Alternatives écartées

- **Prompt écrit à la main par langage** : divergence entre le langage et son prompt, aucun moyen de
  le vérifier.
- **Sortie JSON puis assemblage du programme par du code** : plus fiable pour un modèle minuscule,
  mais déplace de la logique de domaine dans du code de gabarit ; à reconsidérer si un 1B doit être
  visé.
- **Grammaire contrainte** (GBNF) : Ollama ne l'expose pas via son API de chat.
