# Backend Python contractuel

`PythonBackend(registry.prepare(id, session.checker), permissions=...)` prépare
un adaptateur sans importer son code. Les contrats et codecs sont ceux du registre
d'extensions. Les permissions absentes et préconditions non prises en charge
sont refusées explicitement.

`backend.register(natives, "plugin.operation")` autorise une primitive sur une
instance de `NativeRegistry`. Construire ensuite `Session(natives)` et déclarer
`external operation : entree -> sortie = "plugin.operation"`.
Le programme n'obtient aucun accès général à Python.

Chaque invocation valide l'entrée avant import, lance un sous-processus,
charge l'entry point `module:fonction`, puis valide et décode la sortie.
Le plugin reçoit et retourne des données JSON, pas des valeurs du runtime.
Les impressions du plugin ne perturbent pas le protocole.

Le délai du manifeste comprend démarrage, import et appel. À expiration,
le groupe de processus est arrêté et le processus direct récolté.
Aucune relance implicite, même pour une opération idempotente.
Il s'agit d'une isolation de panne, **pas d'un bac à sable de sécurité** :
un plugin autorisé dispose des droits système de Python.

`BackendError`, sous-classe d'`EvaluationError`, porte `extension` et `phase`
(`input`, `import`, `call`, `output`, `process`, `timeout`, etc.).
Le traceur existant enregistre les étapes et erreurs sans absorber les échecs.
Un `check` statique n'appelle jamais le plugin.
