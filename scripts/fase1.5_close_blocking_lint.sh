#!/usr/bin/env bash
# fase1.5_close_blocking_lint.sh - Pasa el job de lint de informativo a bloqueante

echo "=== Fase 1.5: Lint gate -> blocking ==="
echo ""

DIRTY=$(git status --porcelain --untracked-files=no)

if [ -n "$DIRTY" ]; then
    echo "AVISO: hay cambios sin commitear en archivos ya trackeados:"
    echo "$DIRTY"
    echo "Revisa antes de continuar. El script NO va a aplicar cambios."
else
    echo "[OK] working tree limpio, aplicando cambio"

    sed -i '/- name: Run ruff (informational, non-blocking)/,+1{
        s/- name: Run ruff (informational, non-blocking)/- name: Run ruff (blocking)/
        /continue-on-error: true/d
    }' .github/workflows/ci.yml

    echo ""
    echo "=== Diff generado ==="
    git diff .github/workflows/ci.yml

    echo ""
    echo "=== ruff check local (confirmacion final) ==="
    ruff check .
fi

echo ""
echo "=== Revisa el diff arriba. Si el step quedo correcto, corre: ==="
echo "  git add -A"
echo "  git commit -m \"ci: promote ruff lint job from informational to blocking\""
echo "  git push origin main"
