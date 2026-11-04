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

| Exemple | Code Lean | Premier obstacle |
|---|---|---|
| basics/certifiable.hyp | 0 | accepté |
| basics/tour.hyp | 2 | type string |
| knowledge/plaque.hyp | 2 | type string |
| knowledge/regles.hyp | 2 | type float |
| mechanics/units.hyp | 2 | type float |
| mechanics/plate.hyp, après units.hyp | 2 | type float |

Une assertion vérifie que chaque nouveau fichier d'exemple possède un cas
de couverture explicite. Les obstacles ci-dessus sont les premiers rencontrés,
pas nécessairement les seuls (motifs alternatifs, primitives et
polymorphisme peuvent ensuite nécessiter des extensions).

La certification de **tous** les exemples n'est donc pas terminée.
HYP-021 couvre désormais les records nominaux, accès, mises à jour et motifs
partiels (y compris les gardes et les champs permutés). HYP-150 traite les littéraux réels/chaînes
et leurs primitives. Le pont HYP-027 est utilisable, mais son périmètre
global reste ouvert tant que ces formes ne sont pas couvertes sans affaiblir
le checker ni ses théorèmes.

P3 garantit le typage du terme **traduit et accepté dans le fragment Lean**.
Ni le décodage ni le runtime Python n'ont de preuve complète de raffinement :
le chemin de bout en bout combine théorème Lean et frontières testées.
Voir [le catalogue](proprietes.md), pas de nouvelle preuve universelle revendiquée.
