#!/usr/bin/env bash
# Validateurs du projet, lancés à la demande (aucun hook git ne les impose).
#
#   scripts/validate.sh            # rapide : Ruff, Kanban, tests            (~15 s)
#   scripts/validate.sh complet    # tout : pre-commit (linters, Pyright, schémas,
#                                  #   workflows, Lean), tests, audit des axiomes
#   scripts/validate.sh lean       # preuves : lake build, aucun sorry, audit des axiomes
#   scripts/validate.sh graphe     # reconstruit le graphe Graphify et y réinjecte le Kanban
#
# Chaque étape s'exécute même si une précédente échoue ; un résumé final liste les
# échecs et le code de sortie vaut 1 s'il y en a. Le mode « complet » peut corriger
# automatiquement des détails de forme (espaces, fins de fichier, Ruff --fix) : relire
# `git diff` ensuite.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

MODE=${1:-rapide}
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
export PATH="$HOME/.elan/bin:$PATH"

declare -a RESULTS=()
FAILED=0

step() {
    local name=$1
    shift
    printf '\n=== %s\n' "$name"
    if "$@"; then
        RESULTS+=("ok     $name")
    else
        RESULTS+=("ÉCHEC  $name")
        FAILED=1
    fi
}

lean_audit() {
    (cd formal && lake build) || return 1
    ! grep -rnwE 'sorry|admit' formal/Hypomnesis || return 1
    local out
    out=$(cd formal && lake env lean Audit.lean) || return 1
    printf '%s\n' "$out"
    local bad
    bad=$(printf '%s\n' "$out" | grep -oE 'axioms: \[[^]]*\]' | tr -d '[]' | sed 's/axioms: //' \
        | tr ',' '\n' | sed 's/ //g' | grep -vE '^(propext|Quot.sound|Classical.choice)?$' || true)
    if [ -n "$bad" ]; then
        printf 'axiomes non autorisés :\n%s\n' "$bad"
        return 1
    fi
}

graph_refresh() {
    command -v graphify >/dev/null 2>&1 || { echo "graphify absent du PATH"; return 1; }
    graphify update . && "$PY" scripts/kanban.py graph
}

case "$MODE" in
    rapide)
        step "ruff (lint)" "$PY" -m ruff check .
        step "ruff (format)" "$PY" -m ruff format --check .
        step "kanban" "$PY" scripts/kanban.py check
        step "tests" "$PY" -m pytest -q
        ;;
    complet)
        step "pre-commit (tous les linters)" "$PY" -m pre_commit run --all-files --show-diff-on-failure
        step "tests" "$PY" -m pytest -q
        step "lean (audit des axiomes)" lean_audit
        ;;
    lean)
        step "lean (build, sorry, axiomes)" lean_audit
        ;;
    graphe)
        step "graphe Graphify + Kanban" graph_refresh
        ;;
    *)
        echo "mode inconnu : $MODE (rapide | complet | lean | graphe)" >&2
        exit 2
        ;;
esac

printf '\n=== Résumé (%s)\n' "$MODE"
printf '%s\n' "${RESULTS[@]}"
exit "$FAILED"
