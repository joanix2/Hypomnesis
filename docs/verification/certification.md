# Certification CLI et limites du pont Lean

```bash
cd formal && lake build hypomnesis-check && cd ..
hypomnesis check demo/examples/basics/certifiable.hyp --certify
hypomnesis check demo/examples/basics/certifiable.hyp --certify --emit-certificate cert.json
```

`--emit-certificate` seul exporte le Core IR annoté et valide sa structure
JSON ; ce n'est pas une acceptation Lean. `--certify` exige le code zéro
du checker. L'exécutable est choisi par `--checker`, sinon sur PATH, sinon
dans le build local `formal/.lake/build/bin/hypomnesis-check`. Un choix
explicite absent n'entraîne aucun repli sur un autre exécutable.

Le délai fini se règle avec `--checker-timeout` (30 secondes par défaut).
Absence, délai, refus de typage, fragment non pris en charge, certificat
illisible et erreur d'écriture entraînent un échec CLI, jamais un succès
de secours. Les codes internes Lean 1/2/3 sont décrits dans le diagnostic ;
la CLI retourne 1 pour tout refus. Le checker est du code de confiance
choisi par l'hôte, pas un programme fourni par le certificat.

Avec `--format json`, stdout contient **un seul** document final de
diagnostics, y compris si la compilation Python réussit puis Lean refuse.
Les informations d'export et d'acceptation restent sur stderr. Sans chemin
d'export, le certificat temporaire est nettoyé après contrôle ; un export
explicitement demandé reste disponible même si Lean le refuse.
L'entrée `langage.hyp` et les sources suivantes sont certifiées dans la
session effectivement chargée, jamais dans une session préliminaire vide.

## Couverture mesurée des exemples

La CI appelle le vrai pont CLI, injecte une mauvaise élaboration et examine
tous les fichiers de `demo/examples`. Le tableau ci-dessous est une mesure,
**pas une liste d'exemptions assimilées à des succès**.

| Exemple | Code Lean | Résultat |
|---|---|---|
| basics/certifiable.hyp | 0 | accepté |
| basics/tour.hyp | 0 | accepté |
| knowledge/plaque.hyp | 0 | accepté |
| knowledge/regles.hyp | 0 | accepté |
| mechanics/units.hyp | 0 | accepté |
| mechanics/plate.hyp, après units.hyp | 0 | accepté |

Une assertion vérifie que chaque fichier d'exemple possède un cas explicite,
avec acceptation obligatoire, jamais une exemption hors fragment. Cela ne
certifie pas tout nouveau programme possible : les motifs alternatifs imbriqués,
primitives non modélisées et polymorphisme peuvent nécessiter des extensions.

La certification des **six exemples actuels** est vérifiée sans exemption.
HYP-021 couvre désormais les records nominaux, accès, mises à jour et motifs
partiels (y compris les gardes et les champs permutés). HYP-150 couvre les
flottants binary64, les chaînes Unicode et les primitives scalaires nécessaires.
HYP-027 traduit aussi les alternatives racines en chaînes de case et contrôle
la signature des variables par slot. Une garde fausse passe au cas source
suivant, jamais à l'autre alternative du même cas. Le validateur Lean et la CI
exigent chaque acceptation via le checker indépendant et le pont CLI.
Les alternatives imbriquées, alias et primitives non modélisés restent refusés ;
leur normalisation n'est pas prouvée.

## Exhaustivité prouvée et frontière CLI (HYP-022)

`Core.Coverage.check` est une analyse Lean par matrices : spécialisation des
booléens, produits et constructeurs de la signature, matrice par défaut pour
les domaines ouverts. `exhaustive` expose un budget et un résultat
`Option Bool` : seul `some true` établit la couverture ; `none` signale
un budget épuisé. Les bras gardés ne contribuent jamais à cette couverture.
P34 relie le calcul positif à `matchPat` pour toute valeur bien typée.
La sélection conserve au moins un bras, quelles que soient les réponses
booléennes des gardes. Cela ne garantit ni leur terminaison ni l'absence
d'erreur pendant leur évaluation.

P35 porte sur **le véritable `Core.eval`** : tout programme clos muni
d'une dérivation `Coverage.Certified` ne rend jamais `matchFail`, quel que
soit le budget. Le jugement exige des sous-expressions et corps de fonctions
certifiés, y compris les fermetures récursives et les expressions de garde ;
il exclut aussi `stuck`, mais permet timeout et erreurs explicites.
Les exemples prouvent une longueur récursive et une garde fausse qui
passe au bras suivant.

Le checker CLI actuel applique `typeOf`, **pas ce jugement renforcé**.
Ni `--strict`, ni `--certify`, ni leur combinaison n'émet automatiquement
une dérivation `Certified`. Le jugement est conservateur : on ne prouve
pas que tout programme accepté sans avertissement Python est certifiable.
Le corpus différentiel compare 31 matrices ciblées et 240 matrices générées,
plus quatre cas de budget. Il normalise alias et alternatives pour comparer
la couverture, sans prouver leur élaboration ni leur comportement avec gardes.
Il n'établit ni équivalence universelle Python/Lean ni complétude du calcul.

P3 garantit le typage du terme **traduit et accepté dans le fragment Lean**.
Ni le décodage ni le runtime Python n'ont de preuve complète de raffinement :
le chemin de bout en bout combine théorème Lean et frontières testées.
Voir [le catalogue](proprietes.md), pas de nouvelle preuve universelle revendiquée.

## Scalaires et format 1.1

L'export écrit `certificate/1.1.0`. Chaque littéral float fini porte ses
64 bits IEEE dans `bits`, contrôlés contre sa valeur numérique. Cela
préserve notamment le zéro négatif, perdu par le parseur numérique JSON
Lean. Le loader Python lit encore 1.0 et peut réexporter en 1.1 ; Lean
refuse explicitement les anciens littéraux float sans bits, au lieu de
leur attribuer une valeur approximative. Le schéma 1.0 n'est pas modifié.

Arithmétique Float de Lean 4.35 : binary64, pas nombres réels mathématiques.
L'égalité est IEEE (NaN n'est pas égal à lui-même), mais `<`, `<=`, `>` et
`>=` suivent **compare** du runtime : NaN est classé avant les autres valeurs.
La division flottante par zéro conserve inf/NaN et le signe du zéro.
La division entière tronque vers zéro ; division/modulo entiers par zéro
et failwith produisent `Res.error`, distinct de stuck et Match_failure.
Les opérations non inscrites au catalogue fermé restent hors fragment.
