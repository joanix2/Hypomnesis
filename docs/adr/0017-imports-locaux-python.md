# ADR 0017 — Imports locaux avec syntaxe Python

- Statut : acceptée par l'utilisateur (HYP-011).

## Décision

```hyp
import units
import physique.units as mesures
from units import Length
from units import mm as millimetres
```

Les noms pointés désignent des fichiers locaux relativement au fichier
importeur : `units.hyp`, `physique/units.hyp`. Pas de recherche dans le
répertoire courant, de téléchargement, ni d'import Python. Un chemin de
recherche configurable n'est pas ajouté : la résolution locale est le
périmètre arbitré pour cette itération.

Un fichier constitue un espace de noms de ses seuls exports. `import units`
permet `units.Length.mm` si le fichier définit `module Length`. `from`
importe un membre précis, `as` le renomme sans changer son identité typée.
Un chemin pointé sans alias conserve la qualification complète.
Les collisions ambiguës et membres absents sont refusés. `open` ouvre un
module déjà chargé ; aucun import `*`.

Les chemins canoniques dédupliquent les alias et diamants par session.
Les cycles sont refusés avec leur chaîne, sans module partiellement
initialisé. Un échec n'est pas mémorisé comme un chargement réussi.
Un fichier importé ne voit pas les déclarations de son importeur.

## Frontières

Les imports de couches dans `language` restent distincts : ils composent
des langages et ne transmettent pas les permissions d'I/O implicitement.
Les imports de fichiers ne permettent pas de contourner le confinement
des sources d'une couche. Les overlays non enregistrés sont pris en
compte par le LSP. Le mode statique ne lance ni expressions ni adaptateurs.
La CLI conserve également l'origine des programmes M1 passés à `lancer` :
leurs imports sont relatifs à leur fichier, pas au paquet M2 ni au répertoire
courant. Les API qui reçoivent uniquement une chaîne doivent recevoir son
`filename` pour résoudre des imports ; un texte sans origine ne peut pas importer.

La syntaxe du reste du métalangage ne change pas. Les imports sont résolus
avant l'évaluation et élaborés vers les définitions Core existantes, avec
identités internes partagées entre alias ; aucune primitive d'I/O libre
n'est ajoutée au runtime.
