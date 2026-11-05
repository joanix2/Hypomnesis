---
title: "HYP-151 · Cohérence des déclarations language et coloration VS Code"
lane: qa
created: 2026-11-04T23:08:20+01:00
updated: 2026-11-04T23:08:20+01:00
description: "P2 · M · Métalangage et outillage · syntaxe des métadonnées et coloration sur le poste courant"
priority: P2
tags: [metalangage, dsl, outillage, vscode]
---

## Conversation

### user

**Ticket** HYP-151 · **Priorité** P2 · **Taille** M · **Epic** Métalangage et outillage · **Dépend de** HYP-131, HYP-147 · **Labels** vscode, metalangage

la syntaxe est différente et il n'y a pas de coloration syntaxique :

```hyp
language arithmetique = {
  version = "1.0.0";
  description = "Arithmétique entière réutilisable, sans entrée/sortie."
}
```

#### Contexte

Signalement sur [arithmetique/langage.hyp](../../demo/languages/arithmetique/langage.hyp).
L'utilisateur constate une différence de syntaxe et une absence de coloration.
La déclaration language est une forme native introduite par HYP-147 ; ne
pas décider d'une nouvelle syntaxe à la place de l'utilisateur.

#### Tâches proposées

- Comparer la déclaration language aux autres déclarations du métalangage :
  métadonnées, descriptions et imports. Expliciter les différences et proposer
  une harmonisation à faire arbitrer avant tout changement incompatible.
- Reproduire le défaut sur le poste courant : association .hyp, extension
  active, version installée et grammaire embarquée.
- Vérifier la tokenisation réelle du bloc : language, nom déclaré, champs,
  chaînes, opérateurs et ponctuation ; corriger les surfaces manquantes.
- Ajouter un test TextMate du bloc exact et documenter installation/
  rechargement si la grammaire source est correcte mais l'extension inactive
  ou obsolète.

#### Critères d'acceptation

- La différence de syntaxe est expliquée et l'éventuel choix d'harmonisation
  est validé par l'utilisateur, sans migration silencieuse.
- Le fichier est reconnu comme Hypomnesis et sa coloration est vérifiée
  dans un hôte VS Code, pas seulement par lecture du JSON de grammaire.
- Un test couvre la déclaration exacte ci-dessus ; les autres formes
  continuent à être colorées.

#### Fichiers concernés

- `demo/languages/arithmetique/langage.hyp`
- `editors/vscode/`
- `src/hypomnesis/language/grammar/hypomnesis.lark`
- Documentation des déclarations de langage et de l'installation VS Code.

### agent

Signalement enregistré, sans modification de syntaxe ni implémentation.
Constat initial : language est déjà présent dans les mots-clés de la
grammaire TextMate du dépôt. Cela ne prouve pas que cette version de
l'extension est installée/active sur le poste courant ; cette frontière
devra être vérifiée. Le nom déclaré et les métadonnées peuvent aussi
nécessiter des règles dédiées.

### user

### agent

Plan / todo / implement du volet préparatoire Mac, sans migration syntaxique.
L'extension hypomnesis.hypomnesis 0.1.0 est bien installée sur ce poste et
sa grammaire contient déjà language, comme celle du dépôt. Cela n'établit
pas l'état de la fenêtre courante ; absence totale de couleur non reproduite
à ce stade. Le nom minuscule arithmetique et les clés de métadonnées n'ont
en revanche pas de scopes dédiés dans les deux copies.

Ajouter ces scopes dans le seul contexte language, y compris records
imbriqués et commentaires/chaînes, puis tester le bloc exact avec TextMate
et dans un hôte VS Code isolé. Ne pas modifier le parseur ni les exemples.
Comparer ensuite les formes et soumettre l'arbitrage syntaxique à l'humain.
Le ticket reste doing tant que cet arbitrage manque.

### user

### agent

Comparaison pour arbitrage : `language` est une déclaration native de
configuration statique, pas une expression de record ni un module exécuté.
Elle conserve un identifiant minuscule de langage. Ses valeurs sont des
constantes de configuration : `imports` charge des couches/fichiers, alors
que `open Module` ouvre un espace de noms déjà présent. `description` décrit
le langage global ; les commentaires `(** … *)` documentent ses symboles.
Ces distinctions expliquent la différence sans justifier un choix imposé.

Deux formes possibles, sémantique statique inchangée :

**A — conserver la forme record**, avec coloration corrigée :

```hyp
language arithmetique = {
  version = "1.0.0";
  description = "Arithmétique entière réutilisable, sans entrée/sortie."
}
```

**B — rapprocher la configuration de la forme module**, proposition
non acceptée actuellement par le parseur :

```hyp
language arithmetique = struct
  let version = "1.0.0"
  let description = "Arithmétique entière réutilisable, sans entrée/sortie."
end
```

A évite une migration ; B harmonise les délimiteurs et les liaisons avec
les modules, mais exige une ADR, grammaire, diagnostics, documentation et
migration/tests de toutes les déclarations. Dans B, les liaisons resteraient
des constantes de configuration, pas du Python ni des effets évaluables.
Une troisième syntaxe peut être proposée par l'utilisateur. Aucun changement
incompatible engagé avant son choix.

### user

### agent

Volet coloration vérifié : 9 tests Node passent, dont le bloc exact,
retours à la ligne, records imbriqués et accolades dans commentaires/chaînes.
Dans un vrai Extension Host VS Code isolé sur ce Mac : association .hyp,
extension active, tokenisation avec sa contribution chargée, scopes du
bloc exact, diagnostic de typage et correction non enregistrée passent.
Le test ne prétend pas mesurer les couleurs RGB de chaque thème.

VSIX 0.1.1 construit et installé dans le profil courant ; la grammaire
installée est identique octet pour octet à celle vérifiée. L'ancienne
version était 0.1.0, déjà capable de colorer language/chaînes mais pas le
nom et les clés. La fenêtre déjà ouverte peut nécessiter Developer: Reload
Window ; pas de rechargement forcé de la session de travail.

Validation complète verte, documentation d'installation/inspection et
TECHNICAL actualisés. Aucune modification du parseur ni des déclarations
existantes. Ticket non clos : choix A/B/autre encore réservé à l'utilisateur.

### user

### agent

Validation finale complète, rapide et graphe verte après correction du
coût de chargement des contrats embarqués (suivi HYP-133). Le délai
Hypothesis de 200 ms reste inchangé. Le volet coloration peut être committé
indépendamment ; le parseur n'a pas changé. Arbitrage à soumettre dans
le formulaire : A, syntaxe actuelle ; B, configuration statique struct/let/end ;
ou une autre proposition. Le ticket reste doing en attendant cette décision.

### user

Forme B retenue, puis précision : « non remplace l'ancienne forme ».

### agent

Décision appliquée sans coexistence : `language nom = struct let clé = valeur end`.
Les valeurs restent des constantes statiques ; les records imbriqués gardent
leurs accolades, séparateurs et clés éventuellement citées. Les liaisons du
bloc sont nommées par un identifiant minuscule, sans paramètres, récursion,
annotation ni calcul arbitraire. L'ancienne déclaration à accolades sera
refusée par le parseur, pas convertie implicitement.

Plan / todo / implement : nouvelle ADR remplaçant seulement la surface
syntaxique de l'ADR 0013 ; grammaire et transformation vers le même AST ;
migration des déclarations actives, fixtures et documentation ; adaptation
TextMate et vérification Extension Host réel. Tests de rejet de l'ancienne
forme, des doublons et expressions, puis validations complète/rapide/graphe.
Les conversations et ADR historiques restent intactes.

### user

### agent

Remplacement implémenté (ADR 0016) : seule la déclaration struct/let/end
est acceptée. Les huit langages de démonstration, fixtures Python/Codegen/
certificats/LSP et documentation active sont migrés. L'AST et les contrats
statiques restent identiques ; aucun calcul ni chargement Python ajouté.
Les conversations et l'ADR 0013 restent des documents historiques.

Tests : ancienne forme rejetée au parseur et via check JSON avec position
exacte ; doublons extérieurs/imbriqués, calculs/paramètres/récursion/
annotations refusés ; end dans chaînes/commentaires/records sans fermeture
prématurée ; liaisons de métadonnées non exportées. Les tests existants
conservent DAG, diamants, confinement, adaptateurs non importés et procédures.

Onze tests TextMate verts. Hôte VS Code réel : association, activation,
scopes, diagnostic/correction du programme et rejet de l'ancienne déclaration
puis correction non enregistrée vérifiés. Extension 0.1.2 packagée et
installée ; grammaire installée identique à la source. Aucun rechargement
forcé de la fenêtre utilisateur ; Developer: Reload Window si nécessaire.

Validation complète verte (linters/types/schémas, noyau, Codegen, Lean,
audit et 500 termes différentiels), graphe rafraîchi sans appel LLM.
Ticket proposé en QA, jamais en done par l'agent. Dernière validation
rapide et commit local à suivre, sans push.

### user

### agent

Dernière validation rapide verte : Ruff, formatage, 109 tâches Kanban
valides, suites noyau et Codegen. Validation graphe également relancée
après passage en QA. Le commit local regroupe uniquement HYP-151 et sa
migration ; aucun push. Forme finale :

```hyp
language arithmetique = struct
  let version = "1.0.0"
  let description = "Arithmétique entière réutilisable, sans entrée/sortie."
end
```

Le reste du lot Mac reste ouvert ; cette validation ne le déclare pas terminé.

### user
