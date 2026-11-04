=== Catalogue du langage « ventilation » ===
Régulation de température par ventilateur ; procédures écrites en Hypomnesis (effets comme valeurs).

Tu n'utilises que les éléments de ce catalogue. Le programme se termine par `let procedure = …` qui appelle une procédure.

## Module Ventilation
Régulation de la température d'une pièce par un ventilateur.
- Squelette de programme :
    ```
    let installation = {
      Ventilation.capteur = "thermo-1";
      ventilateur = "fan-1";
      budget = 3;
    }
    let procedure = Ventilation.reguler installation
    ```
- Note : le premier champ d'un record est préfixé par le module (`Ventilation.capteur = …`), les autres non ; l'installation se nomme `installation` et la procédure `procedure`

### Type `Ventilation.installation`
Une installation à réguler : un capteur, un ventilateur et un nombre maximal d'actions.
- `capteur : string` — Identifiant du capteur de température.
  - Exemple : « le capteur thermo-1 » → "thermo-1"
- `ventilateur : string` — Identifiant du ventilateur à piloter.
  - Exemple : « le ventilateur fan-7 » → "fan-7"
- `budget : int` — Nombre maximal d'actions (itérations, tentatives) de la régulation.
  - Exemple : « pas plus de 6 tentatives » → 6 ; « une seule action » → 1

### Procédures (valeurs de type `… Effect.t`)

`Ventilation.reguler_avec_confirmation` : Ventilation.installation -> string -> string Effect.t
Régule avec un capteur de confirmation distinct après chaque action.
- Utiliser quand : la demande impose un second capteur de confirmation

`Ventilation.reguler` : Ventilation.installation -> string Effect.t
Régule la température : observe le capteur, règle la vitesse du ventilateur si la température dépasse le seuil, vérifie l'effet, recommence au plus `budget` fois.
- Utiliser quand : « régule », « surveille », « pilote », « maintiens la température »
- Exemple : « régule avec thermo-1 et fan-7, 6 tentatives max » → Ventilation.reguler installation

## Frontières hôte
Contrats du langage : contrats/temperature.read-1.0.0.json, contrats/temperature.reading-1.0.0.json, contrats/fan.set-1.0.0.json, contrats/fan.set.result-1.0.0.json.
Modules adaptateurs déclarés (non importés) : adaptateurs/piece.py.
Les permissions sont accordées par l'hôte, jamais par le programme généré.
