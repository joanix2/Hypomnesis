# ADR 0011 — Démonstrations isolées dans `demo/`

- **Statut :** acceptée
- **Date :** 2026-11-04
- **Précise :** les emplacements du tableau de l'ADR 0008 ; ses règles M3/M2/M1/M0 sont inchangées.

## Contexte

L'utilisateur souhaite distinguer clairement le moteur réutilisable des démonstrations
mécanique et ventilation et nettoyer les résultats d'exécution.

## Décision

- M3 reste dans `src/hypomnesis/`, sans logique métier.
- Les langages M2 livrés comme démonstrations sont dans `demo/languages/`.
- Leurs programmes M1 sont dans `demo/programs/` ; les exemples du métalangage dans
  `demo/examples/`.
- Les sorties M0 par défaut sont dans `demo/sortie/`, ignoré dans Git. Les anciens
  chemins `sortie/` et `sortie-plaque/` restent ignorés pour les exécutions anciennes.
- Les sorties générées existantes sont supprimées, pas déplacées ni versionnées.
- Les tests réutilisent les sources de démonstration et écrivent dans des dossiers temporaires.

## Conséquences

Les chemins documentés, la CI, les certificats et l'extension VS Code suivent ce rangement.
Les chemins relatifs entre un paquet M2 et ses programmes sont préservés.
Le serveur LSP détecte une paire de dossiers voisins `programs/` et `languages/` sous
le workspace, sans imposer `demo/` aux projets externes.
`--sortie` conserve la possibilité de choisir une autre destination.
Les conversations historiques du Kanban et les ADR déjà acceptées ne sont pas réécrites.
