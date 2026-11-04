=== Catalogue du langage « mecanique » ===
Pièces mécaniques simples : plaques, estimation d'épaisseur, contraintes d'élancement et de masse, export de géométrie, mesure ; procédures écrites en Hypomnesis.

Tu n'utilises que les éléments de ce catalogue. Le programme se termine par `let procedure = …` qui appelle une procédure.

## Module Plaque
Plaques d'acier : conception d'une plaque (épaisseur donnée, estimée ou mesurée), validation de ses contraintes puis export de sa géométrie.
- Squelette de programme :
    ```
    let demande = {
      Plaque.nom = "plaque";
      largeur = 100.0;
      hauteur = 50.0;
      epaisseur = None;
      masse_max = 2.0;
    }
    let procedure = Plaque.concevoir demande Plaque.estimateur_regle
    ```
- Note : le premier champ d'un record est préfixé par le module (`Plaque.nom = …`), les autres non ; la demande se nomme `demande` et la procédure `procedure`

### Type `Plaque.demande`
La plaque voulue, telle que la décrit la demande. `None` = valeur inconnue, à déterminer par le langage : ne jamais inventer une valeur absente de la demande.
- `nom : string` — Nom court de la plaque.
  - Par défaut : "plaque"
  - Exemple : « plaque renfort-gauche » → "renfort-gauche" ; sans nom → "plaque"
- `largeur : float` — Largeur de la plaque.
  - Unité : mm (convertir : 1 cm = 10 mm, 1 m = 1000 mm)
  - Exemple : « 7 cm » → 70.0 ; « 0,6 m » → 600.0 ; « 95 × 40 » → largeur 95.0
  - Note : « carrée de 6 cm de côté » → largeur = hauteur = 60.0
- `hauteur : float` — Hauteur de la plaque (deuxième dimension).
  - Unité : mm
  - Exemple : « 95 × 40 » → hauteur 40.0 ; « 9 cm sur 5 cm » → 50.0
- `epaisseur : float option` — Épaisseur, si elle est donnée.
  - Unité : mm
  - Par défaut : None (inconnue : l'estimateur la détermine)
  - Exemple : « épaisseur 6 mm » → Some 6.0 ; « on verra plus tard » → None
- `masse_max : float` — Masse maximale admissible.
  - Unité : kg (convertir : 250 g = 0.25)
  - Par défaut : 1000.0 si aucune limite n'est donnée
  - Exemple : « pas plus de 2,5 kg » → 2.5 ; « moins de 350 g » → 0.35

### Type `Plaque.estimateur`
Un estimateur d'épaisseur : une heuristique métier interchangeable.
- `id : string`
- `confiance : float`
- `estimer : demande -> float`

### Procédures (valeurs de type `… Effect.t`)

`Plaque.concevoir` : Plaque.demande -> Plaque.estimateur -> string Effect.t
Conçoit une plaque : prend l'épaisseur si elle est donnée, sinon l'estime, la résout sous les contraintes d'élancement et de masse, valide la plaque puis exporte sa géométrie (SVG et JSON). Procédure de base, sans mesure.
- Utiliser quand : « crée », « conçois », « dimensionne », « fais », « je veux » une plaque
- Ne pas utiliser quand : la demande parle de mesurer ou contrôler l'épaisseur réelle (pied à coulisse)
- Exemple : « plaque 70 × 55 mm, 0,25 kg max » → Plaque.concevoir demande Plaque.estimateur_regle

`Plaque.concevoir_puis_mesurer` : Plaque.demande -> Plaque.estimateur -> string Effect.t
Conçoit la plaque comme `concevoir`, puis mesure l'épaisseur réelle au pied à coulisse, retire l'estimation et revalide la plaque avec la mesure.
- Utiliser quand : la demande parle de mesurer, contrôler ou réviser l'épaisseur réelle (pied à coulisse)
- Exemple : « plaque 90 × 60 mm, 0,2 kg max, puis contrôle l'épaisseur au pied à coulisse » → Plaque.concevoir_puis_mesurer demande Plaque.estimateur_regle

### Valeurs

`Plaque.estimateur_regle` : Plaque.estimateur
Estimateur par règle : épaisseur ≈ petit côté / 25.
- Utiliser quand : la demande dit « règle » ou « estimateur par règle »
- Par défaut : estimateur à utiliser quand la demande n'en précise aucun

`Plaque.estimateur_abaque` : Plaque.estimateur
Estimateur par abaque : épaisseur lue dans une table selon la surface.
- Utiliser quand : la demande dit « abaque »
