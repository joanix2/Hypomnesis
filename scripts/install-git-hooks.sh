#!/bin/sh
# Installe les hooks git du projet (idempotent). À lancer une fois par clone :
#   ./scripts/install-git-hooks.sh
#
#   - pre-commit : linters et vérification du Kanban (.pre-commit-config.yaml)
#   - post-commit / post-checkout : reconstruction du graphe par Graphify, puis
#     réinjection des tâches du Kanban une fois cette reconstruction terminée
#     (python3 scripts/kanban.py graph --wait, lancé en arrière-plan pour ne pas
#     ralentir le commit ; journal : ~/.cache/hypomnesis-kanban-graph.log).
#
# Désinstallation : supprimer les blocs « kanban-graph-hook » de
# .git/hooks/post-commit et .git/hooks/post-checkout, puis `graphify hook uninstall`
# et `pre-commit uninstall`.
set -eu
cd "$(git rev-parse --show-toplevel)"

PRE_COMMIT=.venv/bin/pre-commit
[ -x "$PRE_COMMIT" ] || PRE_COMMIT=pre-commit
"$PRE_COMMIT" install

if command -v graphify >/dev/null 2>&1; then
    graphify hook install
else
    echo "graphify absent : graphe non reconstruit automatiquement (voir TECHNICAL.md)" >&2
fi

HOOKS_DIR=$(git rev-parse --git-path hooks)
for hook in post-commit post-checkout; do
    file="$HOOKS_DIR/$hook"
    [ -f "$file" ] || printf '#!/bin/sh\n' > "$file"
    if ! grep -q "kanban-graph-hook-start" "$file"; then
        cat >> "$file" <<'HOOK'

# kanban-graph-hook-start
# Réinjecte les tâches du Kanban dans graphify-out/graph.json après la
# reconstruction lancée par Graphify (attend son verrou). Installé par
# scripts/install-git-hooks.sh.
if [ -f scripts/kanban.py ] && [ -d graphify-out ] && command -v python3 >/dev/null 2>&1; then
    mkdir -p "${HOME}/.cache"
    nohup python3 scripts/kanban.py graph --wait >>"${HOME}/.cache/hypomnesis-kanban-graph.log" 2>&1 &
fi
# kanban-graph-hook-end
HOOK
    fi
    chmod +x "$file"
done
echo "hooks installés : pre-commit, post-commit, post-checkout"
